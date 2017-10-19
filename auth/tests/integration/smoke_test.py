import asyncio
import os

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.core.utils.aio import fire


async def get_token(project, creds, scopes):
    with aiohttp.ClientSession() as session:
        token = Token(project, creds, session=session, scopes=scopes)
        result = await token.get()

    assert result is not None


def test_token_is_created():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    task = fire(get_token, project, creds, scopes)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
