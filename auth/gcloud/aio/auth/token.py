"""
Google Cloud auth via service account file
"""
import datetime
import enum
import json
import os
import time
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Union
from urllib.parse import urlencode

import backoff
import cryptography  # pylint: disable=unused-import
import jwt

from .build_constants import BUILD_GCLOUD_REST
from .session import AioSession
# N.B. the cryptography library is required when calling jwt.encrypt() with
# algorithm='RS256'. It does not need to be imported here, but this allows us
# to throw this error at load time rather than lazily during normal operations,
# where plumbing this error through will require several changes to otherwise-
# good error handling.

# Handle differences in exceptions
try:
    # TODO: Type[Exception] should work here, no?
    CustomFileError: Any = FileNotFoundError
except NameError:
    CustomFileError = IOError


# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Response
    from requests import Session
else:
    from aiohttp import ClientResponse as Response  # type: ignore[assignment]
    from aiohttp import ClientSession as Session  # type: ignore[assignment]
    import asyncio


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


def get_service_data(
        service: Optional[Union[str, IO[AnyStr]]]) -> Dict[str, Any]:
    """
    Get the service data dictionary for the current auth method.

    This method is meant to match the official ``google.auth.default()``
    method (or rather, the subset relevant to our use-case). Things such as the
    precedence order of various approaches MUST be maintained. It was last
    updated to match the following commit:

    https://github.com/googleapis/google-auth-library-python/blob/6c1297c4d69ba40a8b9392775c17411253fcd73b/google/auth/_default.py#L504
    """
    # pylint: disable=too-complex
    # _get_explicit_environ_credentials()
    service = service or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not service:
        # _get_gcloud_sdk_credentials()
        cloudsdk_config = os.environ.get('CLOUDSDK_CONFIG')
        if cloudsdk_config is not None:
            sdkpath = cloudsdk_config
        elif os.name != 'nt':
            sdkpath = os.path.join(os.path.expanduser('~'), '.config',
                                   'gcloud')
        else:
            try:
                sdkpath = os.path.join(os.environ['APPDATA'], 'gcloud')
            except KeyError:
                sdkpath = os.path.join(os.environ.get('SystemDrive', 'C:'),
                                       '\\', 'gcloud')

        service = os.path.join(sdkpath, 'application_default_credentials.json')
        set_explicitly = bool(cloudsdk_config)
    else:
        set_explicitly = True

    # skip _get_gae_credentials(): this lib does not support GAEv1, and GAEv2
    # will fallback to the next step anyway.

    try:
        # also support passing IO objects directly rather than strictly paths
        # on disk
        try:
            with open(service,  # type: ignore[arg-type]
                      encoding='utf-8') as f:
                data: Dict[str, Any] = json.loads(f.read())
                return data
        except TypeError:
            data = json.loads(service.read())  # type: ignore[union-attr]
            return data
    except CustomFileError:
        if set_explicitly:
            # only warn users if they have explicitly set the service_file
            # path, otherwise this is an expected code flow
            raise

        # _get_gce_credentials(): when we return {} here, the Token class falls
        # back to using the metadata service
        return {}
    except Exception:  # pylint: disable=broad-except
        return {}


class Token:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, service_file: Optional[Union[str, IO[AnyStr]]] = None,
                 session: Optional[Session] = None,
                 scopes: Optional[List[str]] = None) -> None:
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

        self.session = AioSession(session)
        self.scopes = ' '.join(scopes or [])
        if self.token_type == Type.SERVICE_ACCOUNT and not self.scopes:
            raise Exception('scopes must be provided when token type is '
                            'service account')

        self.access_token: Optional[str] = None
        self.access_token_duration = 0
        self.access_token_acquired_at = datetime.datetime(1970, 1, 1)

        self.acquiring: Optional['asyncio.Future[Any]'] = None

    async def get_project(self) -> Optional[str]:
        project = (os.environ.get('GOOGLE_CLOUD_PROJECT')
                   or os.environ.get('GCLOUD_PROJECT')
                   or os.environ.get('APPLICATION_ID'))

        if self.token_type == Type.GCE_METADATA:
            await self.ensure_token()
            resp = await self.session.get(GCE_ENDPOINT_PROJECT, timeout=10,
                                          headers=GCE_METADATA_HEADERS)

            if not project:
                try:
                    project = await resp.text()
                except (AttributeError, TypeError):
                    project = str(resp.text)

        elif self.token_type == Type.SERVICE_ACCOUNT:
            project = project or self.service_data.get('project_id')

        return project

    async def get(self) -> Optional[str]:
        await self.ensure_token()
        return self.access_token

    async def ensure_token(self) -> None:
        if self.acquiring and not self.acquiring.cancelled():
            await self.acquiring
            return

        if self.access_token:
            now = datetime.datetime.utcnow()
            delta = (now - self.access_token_acquired_at).total_seconds()
            if delta <= self.access_token_duration / 2:
                return

        self.acquiring = asyncio.ensure_future(self.acquire_access_token())
        await self.acquiring

    async def _refresh_authorized_user(self, timeout: int) -> Response:
        payload = urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.service_data['client_id'],
            'client_secret': self.service_data['client_secret'],
            'refresh_token': self.service_data['refresh_token'],
        })

        resp: Response = await self.session.post(  # type: ignore[assignment]
            url=self.token_uri, data=payload, headers=REFRESH_HEADERS,
            timeout=timeout)
        return resp

    async def _refresh_gce_metadata(self, timeout: int) -> Response:
        resp: Response = await self.session.get(  # type: ignore[assignment]
            url=self.token_uri, headers=GCE_METADATA_HEADERS, timeout=timeout)
        return resp

    async def _refresh_service_account(self, timeout: int) -> Response:
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
        })

        resp: Response = await self.session.post(  # type: ignore[assignment]
            self.token_uri, data=payload, headers=REFRESH_HEADERS,
            timeout=timeout)
        return resp

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def acquire_access_token(self, timeout: int = 10) -> None:
        if self.token_type == Type.AUTHORIZED_USER:
            resp = await self._refresh_authorized_user(timeout=timeout)
        elif self.token_type == Type.GCE_METADATA:
            resp = await self._refresh_gce_metadata(timeout=timeout)
        elif self.token_type == Type.SERVICE_ACCOUNT:
            resp = await self._refresh_service_account(timeout=timeout)
        else:
            raise Exception(f'unsupported token type {self.token_type}')

        content = await resp.json()

        self.access_token = str(content['access_token'])
        self.access_token_duration = int(content['expires_in'])
        self.access_token_acquired_at = datetime.datetime.utcnow()
        self.acquiring = None

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'Token':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
