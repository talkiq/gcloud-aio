# pylint: disable=protected-access
from unittest import mock

import pytest
from gcloud.aio.auth.iam import IamClient
from gcloud.aio.auth.token import Token
from gcloud.aio.auth.token import Type


def test_importable():
    assert True


def test_iam_client_init_service_account():
    email = 'sa@example.iam.gserviceaccount.com'
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.SERVICE_ACCOUNT
    token_mock.service_data = {'client_email': email}
    token_mock.impersonation_uri = None

    client = IamClient(token=token_mock)
    assert client.service_account_email == email


def test_iam_client_init_gce_metadata():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.GCE_METADATA
    token_mock.service_data = {}
    token_mock.impersonation_uri = None

    client = IamClient(token=token_mock)
    assert client.service_account_email is None


def test_iam_client_init_impersonated_service_account():
    email = 'impersonated@project.iam.gserviceaccount.com'
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.IMPERSONATED_SERVICE_ACCOUNT
    token_mock.service_data = {}
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        f'serviceAccounts/{email}:generateAccessToken'
    )

    client = IamClient(token=token_mock)
    assert client.service_account_email == email


def test_iam_client_init_token_with_impersonation_uri():
    email = 'delegated@project.iam.gserviceaccount.com'
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.AUTHORIZED_USER
    token_mock.service_data = {}
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        f'serviceAccounts/{email}:generateAccessToken'
    )

    client = IamClient(token=token_mock)
    assert client.service_account_email == email


def test_iam_client_init_unsupported_token_type():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.AUTHORIZED_USER
    token_mock.service_data = {}
    token_mock.impersonation_uri = None

    with pytest.raises(
        TypeError, match='IAM Credentials Client is only valid for use',
    ):
        IamClient(token=token_mock)


def test_iam_client_service_account_email_variations():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.IMPERSONATED_SERVICE_ACCOUNT
    token_mock.service_data = {}

    # Standard IAM endpoint with :generateAccessToken
    email = 'svc@my-prj.iam.gserviceaccount.com'
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/my-prj/'
        f'serviceAccounts/{email}:generateAccessToken'
    )
    client = IamClient(token=token_mock)
    assert client.service_account_email == email

    # Endpoint without :generateAccessToken
    email = 'svc2@my-prj.iam.gserviceaccount.com'
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        f'serviceAccounts/{email}'
    )
    assert client.service_account_email == email

    # With query params and trailing slash
    email = 'svc3@my-prj.iam.gserviceaccount.com'
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        f'serviceAccounts/{email}:generateAccessToken?param=value'
    )
    assert client.service_account_email == email

    # Client email in service_data takes priority
    email = 'primary@my-prj.iam.gserviceaccount.com'
    token_mock.service_data = {'client_email': email}
    assert client.service_account_email == email
