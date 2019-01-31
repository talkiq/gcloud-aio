import datetime

import aiohttp
import pytest
from gcloud.aio.auth import Token


@pytest.mark.asyncio  # type: ignore
async def test_token_is_created(creds: str) -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    async with aiohttp.ClientSession() as session:
        token = Token(service_file=creds, session=session, scopes=scopes)
        result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)


@pytest.mark.asyncio  # type: ignore
async def test_token_does_not_require_session(creds: str) -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    token = Token(service_file=creds, scopes=scopes)
    result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)


@pytest.mark.asyncio  # type: ignore
async def test_token_does_not_require_creds() -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    token = Token(scopes=scopes)
    result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)
