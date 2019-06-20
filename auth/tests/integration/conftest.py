import os

import aiohttp
import pytest


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return 'voiceai-staging'


@pytest.fixture(scope='function')
async def session() -> aiohttp.ClientSession:
    timeout = aiohttp.ClientTimeout(total=10, connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        yield s
