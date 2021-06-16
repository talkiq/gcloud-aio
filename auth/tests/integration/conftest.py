import os

import pytest


@pytest.fixture(scope='module')
def creds() -> str:
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'
