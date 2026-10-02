# pylint: disable=protected-access
from unittest import mock

import pytest
from gcloud.aio.auth.iam import IamClient
from gcloud.aio.auth.token import Token
from gcloud.aio.auth.token import Type


def test_importable():
    assert True


def test_iam_client_init_service_account():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.SERVICE_ACCOUNT
    token_mock.service_data = {'client_email': 'sa@example.iam.gserviceaccount.com'}
    token_mock.impersonation_uri = None

    client = IamClient(token=token_mock)
    assert client.service_account_email == 'sa@example.iam.gserviceaccount.com'


def test_iam_client_init_gce_metadata():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.GCE_METADATA
    token_mock.service_data = {}
    token_mock.impersonation_uri = None

    client = IamClient(token=token_mock)
    assert client.service_account_email is None


def test_iam_client_init_impersonated_service_account():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.IMPERSONATED_SERVICE_ACCOUNT
    token_mock.service_data = {}
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        'serviceAccounts/impersonated@project.iam.gserviceaccount.com:generateAccessToken'
    )

    client = IamClient(token=token_mock)
    assert client.service_account_email == 'impersonated@project.iam.gserviceaccount.com'


def test_iam_client_init_token_with_impersonation_uri():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.AUTHORIZED_USER
    token_mock.service_data = {}
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        'serviceAccounts/delegated@project.iam.gserviceaccount.com:generateAccessToken'
    )

    client = IamClient(token=token_mock)
    assert client.service_account_email == 'delegated@project.iam.gserviceaccount.com'


def test_iam_client_init_unsupported_token_type():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.AUTHORIZED_USER
    token_mock.service_data = {}
    token_mock.impersonation_uri = None

    with pytest.raises(TypeError, match='IAM Credentials Client is only valid for use'):
        IamClient(token=token_mock)


def test_iam_client_service_account_email_variations():
    token_mock = mock.MagicMock(spec=Token)
    token_mock.token_type = Type.IMPERSONATED_SERVICE_ACCOUNT
    token_mock.service_data = {}

    # Standard IAM endpoint with :generateAccessToken
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/my-prj/'
        'serviceAccounts/svc@my-prj.iam.gserviceaccount.com:generateAccessToken'
    )
    client = IamClient(token=token_mock)
    assert client.service_account_email == 'svc@my-prj.iam.gserviceaccount.com'

    # Endpoint without :generateAccessToken
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        'serviceAccounts/svc2@my-prj.iam.gserviceaccount.com'
    )
    assert client.service_account_email == 'svc2@my-prj.iam.gserviceaccount.com'

    # With query params and trailing slash
    token_mock.impersonation_uri = (
        'https://iamcredentials.googleapis.com/v1/projects/-/'
        'serviceAccounts/svc3@my-prj.iam.gserviceaccount.com:generateAccessToken?param=value'
    )
    assert client.service_account_email == 'svc3@my-prj.iam.gserviceaccount.com'

    # Client email in service_data takes priority
    token_mock.service_data = {'client_email': 'primary@my-prj.iam.gserviceaccount.com'}
    assert client.service_account_email == 'primary@my-prj.iam.gserviceaccount.com'
