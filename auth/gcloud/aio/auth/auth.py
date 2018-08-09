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
import jwt


GCLOUD_TOKEN_DURATION = 3600


class Token(object):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, project: str, service_file: str,
                 session: aiohttp.ClientSession = None,
                 scopes: typing.List[str] = None):
        self.project = project

        with open(service_file, 'r') as f:
            service_data_str = f.read()

        self.service_data = json.loads(service_data_str)

        self.session = session
        self.scopes = scopes or []

        self.access_token = None
        self.access_token_duration = None
        self.access_token_acquired_at = None

        self.acquiring = None

    async def get(self):
        await self.ensure_token()
        return self.access_token

    async def ensure_token(self):
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

    def _generate_assertion(self):
        now = int(time.time())
        payload = {
            'aud': self.service_data['token_uri'],
            'exp': now + GCLOUD_TOKEN_DURATION,
            'iat': now,
            'iss': self.service_data['client_email'],
            'scope': ' '.join(self.scopes),
        }

        # N.B. algorithm='RS256' requires an extra 240MB in dependencies...
        return jwt.encode(payload, self.service_data['private_key'],
                          algorithm='RS256')

    async def acquire_access_token(self):
        assertion = self._generate_assertion()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        payload = urlencode({
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        }, quote_via=quote_plus)

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        response = await self.session.post(self.service_data['token_uri'],
                                           data=payload, headers=headers,
                                           params=None, timeout=60)
        content = await response.json()

        if 'error' in content:
            raise Exception(f'got error acquiring token: {content}')

        self.access_token = str(content['access_token'])
        self.access_token_duration = int(content['expires_in'])
        self.access_token_acquired_at = datetime.datetime.now()
        self.acquiring = None
        return True
