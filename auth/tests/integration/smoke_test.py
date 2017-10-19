import asyncio
import os

import aiohttp
import gcloud.aio.auth.Token as Token
from gcloud.aio.core.utils.aio import fire


async def get_token(project, service_file, scopes):
    with aiohttp.ClientSession() as session:
        token = Token(project, service_file, session=session, scopes=scopes)
        result = await token.get()

    assert result is not None


def test_token_is_created():
    project = os.environ['GCLOUD_PROJECT']
    service_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    task = fire(get_token, project, service_file, scopes)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
