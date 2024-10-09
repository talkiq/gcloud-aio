import os

import pytest


@pytest.fixture(scope='module')
def project_name() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def expected_buckets() -> str:
    return {'artifacts.dialpad-oss.appspot.com',
            'dialpad-oss-public-test',
            'dialpad-oss.appspot.com',
            'staging.dialpad-oss.appspot.com'}


@pytest.fixture(scope='module')
def bucket_name() -> str:
    return 'dialpad-oss-public-test'


@pytest.fixture(scope='module')
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']
