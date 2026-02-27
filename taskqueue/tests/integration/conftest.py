# pylint: disable=redefined-outer-name
import os

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'slow: marks tests as slow (deselect with `-m "not slow"`)',
    )


@pytest.fixture(scope='module')
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def push_queue_name() -> str:
    return 'public-test-push'


@pytest.fixture(scope='module')
def push_queue_location() -> str:
    return 'us-west2'
