import os

import pytest


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']
