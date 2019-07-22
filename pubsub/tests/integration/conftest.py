import os

import pytest


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')  # type: ignore
def subscription_name() -> str:
    return 'public_test'


@pytest.fixture(scope='module')  # type: ignore
def topic_name() -> str:
    return 'public_test'
