import os

import aiohttp
import pytest
from gcloud.aio.auth import Token


@pytest.mark.asyncio
async def test_token_is_created():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    async with aiohttp.ClientSession() as session:
        token = Token(project, creds, session=session, scopes=scopes)
        result = await token.get()

    assert result is not None
