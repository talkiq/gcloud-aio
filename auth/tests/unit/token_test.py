import asyncio
import io
import json
from unittest import mock

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST
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
async def test_external_account_as_io():
    service_data = {
        'type': 'external_account',
        'audience': '//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/pool/subject',
        'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt',
        'token_url': 'https://sts.googleapis.com/v1/token',
        'credential_source': {
            'type': 'url',
            'url': 'http://169.254.169.254/metadata/identity/oauth2/token',
            'headers': {'Metadata': 'true'},
        },
    }

    service_file = io.StringIO(f'{json.dumps(service_data)}')
    t = token.BaseToken(service_file=service_file)

    assert t.token_type == token.Type.EXTERNAL_ACCOUNT
    assert t.token_uri == 'https://sts.googleapis.com/v1/token'


@pytest.mark.asyncio
async def test_external_account_missing_required_fields():
    service_data = {
        'type': 'external_account',
        'audience': '//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/pool/subject',
        'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt',
        # Missing token_url and credential_source
    }

    service_file = io.StringIO(f'{json.dumps(service_data)}')
    with mock.patch(
        'gcloud.aio.auth.token.get_service_data', return_value=service_data
    ):
        with pytest.raises(
            ValueError, match='External account credentials missing required fields'
        ):
            await token.Token(service_file=service_file).get()


@pytest.mark.asyncio
async def test_external_account_token_refresh():
    service_data = {
        'type': 'external_account',
        'audience': '//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/pool/subject',
        'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt',
        'token_url': 'https://sts.googleapis.com/v1/token',
        'credential_source': {
            'type': 'url',
            'url': 'http://169.254.169.254/metadata/identity/oauth2/token',
            'headers': {'Metadata': 'true'},
        },
    }

    service_file = io.StringIO(f'{json.dumps(service_data)}')
    t = token.Token(service_file=service_file)

    # Mock the session to return a subject token
    mock_response = mock.AsyncMock()
    mock_response.status = 200
    mock_response.text = 'subject_token_123'
    t.session.get = mock.AsyncMock(return_value=mock_response)

    # Mock the token exchange response
    mock_token_response = mock.AsyncMock()
    mock_token_response.status = 200
    mock_token_response.json = mock.AsyncMock(
        return_value={'access_token': 'access_token_123', 'expires_in': 3600}
    )
    t.session.post = mock.AsyncMock(return_value=mock_token_response)

    # Test token refresh
    token_response = await t._refresh_external_account(timeout=10)
    assert token_response.value == 'access_token_123'
    assert token_response.expires_in == 3600

    # Verify the correct requests were made
    t.session.get.assert_called_once_with(
        'http://169.254.169.254/metadata/identity/oauth2/token',
        headers={'Metadata': 'true'},
        timeout=10,
    )

    t.session.post.assert_called_once()
    call_args = t.session.post.call_args
    assert call_args[0][0] == 'https://sts.googleapis.com/v1/token'


@pytest.mark.asyncio
async def test_external_account_credential_source_types():
    # Test URL credential source
    url_source = {
        'type': 'url',
        'url': 'http://example.com/token',
        'headers': {'Authorization': 'Bearer secret'},
    }
    t = token.Token()
    mock_response = mock.AsyncMock()
    mock_response.status = 200
    mock_response.text = 'token_from_url'
    t.session.get = mock.AsyncMock(return_value=mock_response)
    token_value = await t._get_subject_token(url_source, timeout=10)
    assert token_value == 'token_from_url'

    # Test file credential source
    file_source = {'type': 'file', 'file': 'test_token.txt'}
    with mock.patch('builtins.open', mock.mock_open(read_data='token_from_file')):
        token_value = await t._get_subject_token(file_source, timeout=10)
        assert token_value == 'token_from_file'

    # Test environment credential source
    env_source = {'type': 'environment', 'environment_id': 'TEST_TOKEN'}
    with mock.patch.dict('os.environ', {'TEST_TOKEN': 'token_from_env'}):
        token_value = await t._get_subject_token(env_source, timeout=10)
        assert token_value == 'token_from_env'

    # Test invalid credential source type
    invalid_source = {'type': 'invalid'}
    with pytest.raises(ValueError, match='Unsupported credential source type'):
        await t._get_subject_token(invalid_source, timeout=10)


# pylint: disable=too-complex
if BUILD_GCLOUD_REST:
    pass
else:

    @pytest.mark.asyncio
    async def test_acquiring_refresh_called_once():
        t = token.BaseToken()
        t.refresh = mock.AsyncMock()

        # Use a future so we can control when refresh returns
        future = asyncio.Future()

        async def refresh(timeout):  # pylint: disable=unused-argument
            return await future

        t.refresh.side_effect = refresh

        # Both tasks should try to acquire a token and block for the same
        # refresh function
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
        t.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_acquiring_cancellation():
        t = token.BaseToken()
        t.acquire_access_token = mock.AsyncMock()

        # If we hit a timeout the first time, an error should return
        t.acquire_access_token.side_effect = asyncio.TimeoutError()
        with pytest.raises(asyncio.TimeoutError):
            await t.get()

        assert t.acquiring.done(), 'Acquiring should be done after timeout'
        assert not t.access_token, 'Token should not be set after timeout'

        # If the token timed out last time, it should retry instead of
        # trying the timed out coroutine again
        t.acquire_access_token.side_effect = None
        t.acquire_access_token.return_value = None
        await t.get()
