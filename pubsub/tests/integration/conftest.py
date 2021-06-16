import os

import pytest


@pytest.fixture(scope='module')
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def subscription_name() -> str:
    return 'public_test'


@pytest.fixture(scope='module')
def topic_name() -> str:
    return 'public_test'
