import os

import pytest


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')  # type: ignore
def kind() -> str:
    return 'public_test'


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')  # type: ignore
def export_bucket_name() -> str:
    return 'dialpad-oss-public-test'
