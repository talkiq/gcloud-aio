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
def task_queue() -> str:
    return 'public-test'
