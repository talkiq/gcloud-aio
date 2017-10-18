"""
Google Cloud auth via service account file
"""
import datetime
import time
import typing

import aiohttp
import jwt
from gcloud.aio.core.http import post
from gcloud.aio.core.utils.aio import auto
from gcloud.aio.core.utils.jason import extract_json_fields
from gcloud.aio.core.utils.jason import json_read


ScopeList = typing.List[str]

JWT_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
GCLOUD_TOKEN_DURATION = 3600
MISMATCH = "Project name passed to Token does not match service_file's " \
           'project_id.'


async def acquire_token(session: aiohttp.ClientSession,
                        service_data: dict,
                        scopes: ScopeList = None):

    url, assertion = generate_assertion(service_data, scopes)

    payload = {
        'grant_type': JWT_GRANT_TYPE,
        'assertion': assertion
    }

    _status, content = await post(
        url,
        payload,
        headers={'content-type': 'application/x-www-form-urlencoded'},
        timeout=60,
        urlencoded=True,
        json_response=True,
        session=session
    )

    data = extract_json_fields(
        content, (
            ('access_token', str),
            ('expires_in', int)
        )
    )

    return data


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
        self.service_data = json_read(service_file)

        # sanity check
        assert self.project == self.service_data['project_id'], MISMATCH

        self.scopes = scopes or []

        self.session = session
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

            self.acquiring = self.acquire_access_token()

            await self.acquiring

        else:

            now = datetime.datetime.now()
            delta = (now - self.access_token_acquired_at).total_seconds()

            if delta > self.access_token_duration / 2:

                self.acquiring = self.acquire_access_token()

                await self.acquiring

    @auto
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


# async def smoke(project, service_file, scopes):

#     import aiohttp

#     with aiohttp.ClientSession() as session:

#         token = Token(
#             project,
#             service_file,
#             session=session,
#             scopes=scopes
#         )

#         result = await token.get()

#     print('success: {}'.format(result))


# if __name__ == '__main__':

#     import asyncio
#     import sys

#     from utils.aio import fire

#     args = sys.argv[1:]

#     if not args or args[0] != 'smoke':
#         exit(1)

#     project = 'talkiq-integration'
#     service_file = 'service-integration.json'
#     scopes = ['https://www.googleapis.com/auth/taskqueue']

#     task = fire(
#         smoke,
#         project,
#         service_file,
#         scopes
#     )

#     loop = asyncio.get_event_loop()

#     loop.run_until_complete(task)
