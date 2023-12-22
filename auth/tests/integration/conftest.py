import os

import pytest


@pytest.fixture(scope='module')
def creds() -> str:
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def delegate() -> str:
    return ('gcloud-ai'  # break here to avoid mangling during gcloud-rest gen
            'o-delegate@dialpad-oss.iam.gserviceaccount.com')


@pytest.fixture(scope='module')
def target_principal() -> str:
    return ('gcloud-ai'  # break here to avoid mangling during gcloud-rest gen
            'o-target-principal@dialpad-oss.iam.gserviceaccount.com')


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'
