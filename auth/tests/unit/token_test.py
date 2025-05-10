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
async def test_acquiring_refresh_called_once():
    t = token.BaseToken()
    t.refresh = mock.AsyncMock()

    async def refresh(timeout):  # pylint: disable=unused-argument
        return token.TokenResponse(
            value='fake_token',
            expires_in=3600,
        )
    t.refresh.side_effect = refresh

    task1 = await t.get()
    task2 = await t.get()
    assert task1 == task2, 'Token should be cached and reused'
    t.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_acquiring_cancellation():
    t = token.BaseToken()
    t.acquire_access_token = mock.AsyncMock()

    # If we hit an exception the first time, an error should return
    t.acquire_access_token.side_effect = ValueError()
    with pytest.raises(ValueError):
        await t.get()

    assert t.acquiring.done(), 'Acquiring should be done after timeout'
    assert not t.access_token, 'Token should not be set after timeout'

    # If the token timed out last time, it should retry instead of
    # trying the timed out coroutine again
    t.acquire_access_token.side_effect = None
    t.acquire_access_token.return_value = None
    await t.get()
