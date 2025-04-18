import asyncio
import io
import json
from unittest import mock

import pytest
from gcloud.aio.auth import token


@pytest.mark.asyncio
async def test_service_as_io():
    # pylint: disable=line-too-long
    service_data = {
        'type': 'service_account',
        'project_id': 'random-project-123',
        'private_key_id': '399asdfsdf92923k32423a9f9sdf',
        'private_key': '-----BEGIN PRIVATE KEY-----\nABCDF012923949394239492349234923==\n-----END PRIVATE KEY-----\n',
        'client_email': 'gcloud-aio-test@random-project-123.iam.gserviceaccount.com',
        'client_id': '2384283429349234293',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/gcloud-aio%40random-project-123.iam.gserviceaccount.com',
    }

    service_file = io.StringIO(f'{json.dumps(service_data)}')
    t = token.BaseToken(service_file=service_file)

    assert t.token_type == token.Type.SERVICE_ACCOUNT
    assert t.token_uri == 'https://oauth2.googleapis.com/token'
    assert await t.get_project() == 'random-project-123'


@pytest.mark.asyncio
@mock.patch('gcloud.aio.auth.token.BaseToken.refresh',
            new_callable=mock.AsyncMock)
async def test_acquiring_refresh_called_once(refresh_mock: mock.AsyncMock):
    t = token.BaseToken()

    # Use a future so we can control when refresh returns
    future = asyncio.Future()

    async def refresh(timeout):
        return await future
    refresh_mock.side_effect = refresh

    # Both tasks should try to acquire a token and block for the same refresh
    # function
    task1 = asyncio.create_task(t.get())
    await asyncio.sleep(0)  # Let the task run

    task2 = asyncio.create_task(t.get())
    await asyncio.sleep(0)  # Let the task run

    # Now set the result of the future, which should unblock both tasks
    future.set_result(
        token.TokenResponse(
            value='fake_token',
            expires_in=3600,
        )
    )
    assert await task1 == await task2, 'Token should be cached and reused'
    refresh_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch('gcloud.aio.auth.token.BaseToken.acquire_access_token',
            new_callable=mock.AsyncMock)
async def test_acquiring_cancellation(acquire_access_token_mock):
    t = token.BaseToken()

    # If we hit a timeout the first time, an error should return
    acquire_access_token_mock.side_effect = asyncio.TimeoutError()
    with pytest.raises(asyncio.TimeoutError):
        await t.get()

    # If the token timed out last time, it should retry instead of trying the
    # timed out coroutine again
    acquire_access_token_mock.side_effect = None
    acquire_access_token_mock.return_value = None
    await t.get()
