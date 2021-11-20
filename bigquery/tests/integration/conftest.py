import os

import pytest


@pytest.fixture(scope='module')
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def dataset() -> str:
    return 'public_test'


@pytest.fixture(scope='module')
def table() -> str:
    return 'public_test'


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def export_bucket_name() -> str:
    return 'dialpad-oss-public-test'
