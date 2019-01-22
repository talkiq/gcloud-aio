import aiohttp
import pytest
from gcloud.aio.auth import Token


@pytest.mark.asyncio
async def test_token_is_created(creds, project):
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    async with aiohttp.ClientSession() as session:
        token = Token(project, creds, session=session, scopes=scopes)
        result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration is not None
    assert token.access_token_acquired_at is not None


@pytest.mark.asyncio
async def test_token_does_not_require_session(creds, project):
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    token = Token(project, creds, scopes=scopes)
    result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration is not None
    assert token.access_token_acquired_at is not None
