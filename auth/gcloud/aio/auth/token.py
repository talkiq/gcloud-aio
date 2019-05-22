"""
Google Cloud auth via service account file
"""
import asyncio
import datetime
import enum
import json
import os
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import quote_plus
from urllib.parse import urlencode

import aiohttp
import backoff
import jwt


GCE_METADATA_BASE = 'http://metadata.google.internal/computeMetadata/v1'
GCE_METADATA_HEADERS = {'metadata-flavor': 'Google'}
GCE_ENDPOINT_PROJECT = (f'{GCE_METADATA_BASE}/project/project-id')
GCE_ENDPOINT_TOKEN = (f'{GCE_METADATA_BASE}/instance/service-accounts'
                      '/default/token?recursive=true')
GCLOUD_TOKEN_DURATION = 3600
REFRESH_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


class Type(enum.Enum):
    AUTHORIZED_USER = 'authorized_user'
    GCE_METADATA = 'gce_metadata'
    SERVICE_ACCOUNT = 'service_account'


def get_service_data(service: Optional[str]) -> Dict[str, Any]:
    service = service or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not service:
        cloudsdk_config = os.environ.get('CLOUDSDK_CONFIG')
        sdkpath = (cloudsdk_config
                   or os.path.join(os.path.expanduser('~'), '.config',
                                   'gcloud'))
        service = os.path.join(sdkpath, 'application_default_credentials.json')
        set_explicitly = bool(cloudsdk_config)
    else:
        set_explicitly = True

    try:
        with open(service, 'r') as f:
            data: Dict[str, Any] = json.loads(f.read())
            return data
    except FileNotFoundError:
        if set_explicitly:
            # only warn users if they have explicitly set the service_file path
            raise

        return {}
    except Exception:  # pylint: disable=broad-except
        return {}


class Token:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, service_file: Optional[str] = None,
                 session: aiohttp.ClientSession = None,
                 scopes: List[str] = None) -> None:
        self.service_data = get_service_data(service_file)
        if self.service_data:
            self.token_type = Type(self.service_data['type'])
            self.token_uri = self.service_data.get(
                'token_uri', 'https://oauth2.googleapis.com/token')
        else:
            # At this point, all we can do is assume we're running somewhere
            # with default credentials, eg. GCE.
            self.token_type = Type.GCE_METADATA
            self.token_uri = GCE_ENDPOINT_TOKEN

        self.session = session
        self.scopes = ' '.join(scopes or [])
        if self.token_type == Type.SERVICE_ACCOUNT and not self.scopes:
            raise Exception('scopes must be provided when token type is '
                            'service account')

        self.access_token: Optional[str] = None
        self.access_token_duration = 0
        self.access_token_acquired_at = datetime.datetime(1970, 1, 1)

        self.acquiring: Optional[asyncio.Future] = None

    async def get_project(self) -> Optional[str]:
        project = (os.environ.get('GOOGLE_CLOUD_PROJECT')
                   or os.environ.get('GCLOUD_PROJECT')
                   or os.environ.get('APPLICATION_ID'))

        if self.token_type == Type.GCE_METADATA:
            await self.ensure_token()
            resp = await self.session.get(GCE_ENDPOINT_PROJECT, timeout=10,
                                          headers=GCE_METADATA_HEADERS)
            resp.raise_for_status()
            project = project or (await resp.text())
        elif self.token_type == Type.SERVICE_ACCOUNT:
            project = project or self.service_data.get('project_id')

        return project

    async def get(self) -> Optional[str]:
        await self.ensure_token()
        return self.access_token

    async def ensure_token(self) -> None:
        if self.acquiring:
            await self.acquiring
            return

        if not self.access_token:
            self.acquiring = asyncio.ensure_future(self.acquire_access_token())
            await self.acquiring
            return

        now = datetime.datetime.now()
        delta = (now - self.access_token_acquired_at).total_seconds()
        if delta <= self.access_token_duration / 2:
            return

        self.acquiring = asyncio.ensure_future(self.acquire_access_token())
        await self.acquiring

    async def _refresh_authorized_user(self,
                                       timeout: int) -> aiohttp.ClientResponse:
        payload = urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.service_data['client_id'],
            'client_secret': self.service_data['client_secret'],
            'refresh_token': self.service_data['refresh_token'],
        }, quote_via=quote_plus)

        return await self.session.post(self.token_uri, data=payload,
                                       headers=REFRESH_HEADERS,
                                       timeout=timeout)

    async def _refresh_gce_metadata(self,
                                    timeout: int) -> aiohttp.ClientResponse:
        return await self.session.get(self.token_uri,
                                      headers=GCE_METADATA_HEADERS,
                                      timeout=timeout)

    async def _refresh_service_account(self,
                                       timeout: int) -> aiohttp.ClientResponse:
        now = int(time.time())
        assertion_payload = {
            'aud': self.token_uri,
            'exp': now + GCLOUD_TOKEN_DURATION,
            'iat': now,
            'iss': self.service_data['client_email'],
            'scope': self.scopes,
        }

        # N.B. algorithm='RS256' requires an extra 240MB in dependencies...
        assertion = jwt.encode(assertion_payload,
                               self.service_data['private_key'],
                               algorithm='RS256')
        payload = urlencode({
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        }, quote_via=quote_plus)

        return await self.session.post(self.token_uri, data=payload,
                                       headers=REFRESH_HEADERS,
                                       timeout=timeout)

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)  # type: ignore
    async def acquire_access_token(self, timeout: int = 10) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=timeout,
                                                 read_timeout=timeout)

        if self.token_type == Type.AUTHORIZED_USER:
            resp = await self._refresh_authorized_user(timeout=timeout)
        elif self.token_type == Type.GCE_METADATA:
            resp = await self._refresh_gce_metadata(timeout=timeout)
        elif self.token_type == Type.SERVICE_ACCOUNT:
            resp = await self._refresh_service_account(timeout=timeout)
        else:
            raise Exception(f'unsupported token type {self.token_type}')

        resp.raise_for_status()
        content = await resp.json()

        self.access_token = str(content['access_token'])
        self.access_token_duration = int(content['expires_in'])
        self.access_token_acquired_at = datetime.datetime.now()
        self.acquiring = None
