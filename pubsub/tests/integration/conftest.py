import os

import pytest


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return 'voiceai-staging'


@pytest.fixture(scope='module')  # type: ignore
def subscription() -> str:
    return 'public_test'


@pytest.fixture(scope='module')  # type: ignore
def topic() -> str:
    return 'public_test'
