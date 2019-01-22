"""
Google Cloud auth via service account file
"""
import asyncio
import datetime
import json
import time
import typing
from urllib.parse import quote_plus
from urllib.parse import urlencode

import aiohttp
import backoff
import jwt


GCLOUD_TOKEN_DURATION = 3600
SERVICE_ACCOUNT = 'service_account'
DEFAULT_ACCOUNT = 'authorized_user'


class Token:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, project: str, service_file: str,
                 session: aiohttp.ClientSession = None,
                 scopes: typing.List[str] = None) -> None:
        self.project = project

        with open(service_file, 'r') as f:
            service_data_str = f.read()

        self.service_data = json.loads(service_data_str)
        self.account_type = self.service_data['type']
        self.token_uri = self.service_data.get(
            'token_uri', 'https://oauth2.googleapis.com/token')

        self.session = session
        self.scopes = scopes or []

        self.access_token: typing.Optional[str] = None
        self.access_token_duration = 0
        self.access_token_acquired_at = datetime.datetime(1970, 1, 1)

        self.acquiring: typing.Optional[asyncio.Future] = None

    async def get(self) -> typing.Optional[str]:
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

    def _default_account_payload(self) -> str:
        return urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.service_data['client_id'],
            'client_secret': self.service_data['client_secret'],
            'refresh_token': self.service_data['refresh_token'],
        }, quote_via=quote_plus)

    def _service_account_payload(self) -> str:
        now = int(time.time())
        assertion_payload = {
            'aud': self.service_data['token_uri'],
            'exp': now + GCLOUD_TOKEN_DURATION,
            'iat': now,
            'iss': self.service_data['client_email'],
            'scope': ' '.join(self.scopes),
        }

        # N.B. algorithm='RS256' requires an extra 240MB in dependencies...
        assertion = jwt.encode(assertion_payload,
                               self.service_data['private_key'],
                               algorithm='RS256')

        return urlencode({
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        }, quote_via=quote_plus)

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)  # type: ignore
    async def acquire_access_token(self) -> bool:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        if self.account_type == SERVICE_ACCOUNT:
            payload = self._service_account_payload()
        elif self.account_type == DEFAULT_ACCOUNT:
            payload = self._default_account_payload()
        else:
            return False

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        resp = await self.session.post(self.token_uri,
                                       data=payload, headers=headers,
                                       params=None, timeout=10)
        resp.raise_for_status()
        content = await resp.json()

        self.access_token = str(content['access_token'])
        self.access_token_duration = int(content['expires_in'])
        self.access_token_acquired_at = datetime.datetime.now()
        self.acquiring = None
        return True
