import datetime

import aiohttp
import pytest
from gcloud.aio.auth import IamCredentialsClient
from gcloud.aio.auth import Token
from gcloud.aio.auth.utils import encode


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


@pytest.mark.asyncio  # type: ignore
async def test_sign_blob(creds: str) -> None:
    data = 'Testing Can be confidential!'
    payload = encode(data)

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:

        iam_credentials = IamCredentialsClient(service_file=creds, session=s)
        signed_data = iam_credentials.sign_blob(payload)
        assert signed_data  # TODO(nick): How do we verify data is signed?

