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


ScopeList = typing.List[str]

JWT_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
GCLOUD_TOKEN_DURATION = 3600
MISMATCH = "Project name passed to Token does not match service_file's " \
           'project_id.'


async def acquire_token(session: aiohttp.ClientSession, service_data: dict,
                        scopes: ScopeList = None):
    url, assertion = generate_assertion(service_data, scopes)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    payload = urlencode({
        'assertion': assertion,
        'grant_type': JWT_GRANT_TYPE,
    }, quote_via=quote_plus)

    response = await session.post(url, data=payload, headers=headers,
                                  params=None, timeout=60)
    content = await response.json()

    if 'error' in content:
        raise Exception(f'got error acquiring token: {content}')

    return {
        'access_token': str(content['access_token']),
        'expires_in': int(content['expires_in']),
    }


def generate_assertion(service_data: dict, scopes: ScopeList = None):

    payload = make_gcloud_oauth_body(
        service_data['token_uri'],
        service_data['client_email'],
        scopes
    )

    jwt_token = jwt.encode(
        payload,
        service_data['private_key'],
        algorithm='RS256'  # <-- this means we need 240MB in additional
                           # dependencies...
    )

    return service_data['token_uri'], jwt_token


def make_gcloud_oauth_body(uri: str, client_email: str, scopes: ScopeList):

    now = int(time.time())

    return {
        'aud': uri,
        'exp': now + GCLOUD_TOKEN_DURATION,
        'iat': now,
        'iss': client_email,
        'scope': ' '.join(scopes),
    }


class Token(object):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, project: str, service_file: str,
                 session: aiohttp.ClientSession = None,
                 scopes: ScopeList = None):

        self.project = project

        with open(service_file, 'r') as f:
            service_data_str = f.read()

        self.service_data = json.loads(service_data_str)

        # sanity check
        assert self.project == self.service_data['project_id'], MISMATCH

        self.scopes = scopes or []

        self.session = session or aiohttp.ClientSession()
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

        elif not self.access_token:

            self.acquiring = asyncio.ensure_future(self.acquire_access_token())

            await self.acquiring

        else:

            now = datetime.datetime.now()
            delta = (now - self.access_token_acquired_at).total_seconds()

            if delta > self.access_token_duration / 2:

                self.acquiring = asyncio.ensure_future(
                    self.acquire_access_token())

                await self.acquiring

    async def acquire_access_token(self):

        data = await acquire_token(
            self.session,
            self.service_data,
            self.scopes
        )

        access_token = data['access_token']
        expires_in = data['expires_in']

        self.access_token = access_token
        self.access_token_duration = expires_in
        self.access_token_acquired_at = datetime.datetime.now()
        self.acquiring = None

        return True
