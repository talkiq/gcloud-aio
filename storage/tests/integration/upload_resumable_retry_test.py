"""
Resumable upload retries against real connection faults.

Runs the upload through a Toxiproxy (https://github.com/Shopify/toxiproxy) in
front of the storage emulator, so the retry loop sees genuine dropped and reset
connections rather than mocked exceptions. Needs both an emulator
(`STORAGE_EMULATOR_HOST`) and a Toxiproxy server (`TOXIPROXY_HOST`, its API
URL), and is skipped otherwise; see the `python-emulator-storage` executor in
`.circleci/config.yml` and `.github/CONTRIBUTING.rst`.
"""
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from typing import Any
from urllib.parse import urlsplit

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage
from gcloud.aio.storage import storage as aio_storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import ConnectionError as ConnectionFailure
    from requests import HTTPError as ResponseError
    from requests import Session
else:
    from aiohttp import ClientConnectionError as ConnectionFailure
    from aiohttp import ClientResponseError as ResponseError
    from aiohttp import ClientSession as Session

# pylint: disable=redefined-outer-name

EMULATOR_HOST = os.environ.get('STORAGE_EMULATOR_HOST')
TOXIPROXY_HOST = os.environ.get('TOXIPROXY_HOST')

PROXY_NAME = 'fake-gcs'
# Where Toxiproxy listens, and how this test reaches it.
PROXY_LISTEN = '0.0.0.0:4444'
PROXY_URL = 'http://localhost:4444'
# Where Toxiproxy reaches the emulator from; differs from the emulator's
# address as seen by the tests if the two don't share a network.
PROXY_UPSTREAM = (
    os.environ.get('TOXIPROXY_UPSTREAM')
    or (urlsplit(EMULATOR_HOST).netloc if EMULATOR_HOST else '')
)

MAX_ATTEMPTS = 5
# Large enough that cutting the request off after a few KiB lands mid-body.
DATA = os.urandom(256 * 1024)


def toxiproxy(
        method: str, path: str, body: dict[str, object] | None = None,
) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f'{TOXIPROXY_HOST}{path}', data=data, method=method,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        content = response.read()
    return json.loads(content) if content else None


def clear_toxics() -> None:
    toxics = toxiproxy('GET', f'/proxies/{PROXY_NAME}/toxics')
    for toxic in toxics or []:
        toxiproxy('DELETE', f'/proxies/{PROXY_NAME}/toxics/{toxic["name"]}')


def add_toxic(toxic_type: str, **attributes: int) -> None:
    # Only the request direction: the emulator still sees (part of) the body.
    toxiproxy(
        'POST', f'/proxies/{PROXY_NAME}/toxics',
        {
            'name': toxic_type, 'type': toxic_type, 'stream': 'upstream',
            'toxicity': 1.0, 'attributes': attributes,
        },
    )


def status_of(error: Exception) -> int:
    if BUILD_GCLOUD_REST:
        return error.response.status_code  # type: ignore[attr-defined]
    return error.status  # type: ignore[attr-defined]


class Upload:
    """What the `faulty_upload` fixture hands to a test."""

    def __init__(self) -> None:
        self.delays: list[float] = []
        # Whether a retry's backoff clears the fault, ie. whether it was
        # transient.
        self.heal = True


@pytest.fixture(scope='module')
def fault_proxy():
    if not (EMULATOR_HOST and TOXIPROXY_HOST):
        pytest.skip('needs STORAGE_EMULATOR_HOST and TOXIPROXY_HOST')

    deadline = time.monotonic() + 60
    while True:
        try:
            toxiproxy('GET', '/version')
            break
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)

    try:
        toxiproxy('DELETE', f'/proxies/{PROXY_NAME}')
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    toxiproxy(
        'POST', '/proxies',
        {
            'name': PROXY_NAME, 'listen': PROXY_LISTEN,
            'upstream': PROXY_UPSTREAM, 'enabled': True,
        },
    )
    try:
        yield
    finally:
        toxiproxy('DELETE', f'/proxies/{PROXY_NAME}')


@pytest.fixture(scope='function')
def faulty_upload(fault_proxy, monkeypatch):
    """
    Routes the resumable upload's data requests through the proxy, and replaces
    the retry backoff so that it clears the fault (unless a test says it is
    persistent) without actually waiting.
    """
    # pylint: disable=unused-argument
    upload = Upload()

    async def fake_sleep(delay):
        upload.delays.append(delay)
        if upload.heal:
            clear_toxics()

    monkeypatch.setattr(aio_storage, 'sleep', fake_sleep)

    # The emulator hands back its own address as the session URI; point the
    # data requests at the proxy instead (initiating the upload and everything
    # else still goes straight to the emulator).
    emulator = urlsplit(EMULATOR_HOST)
    original = aio_storage.Storage._initiate_upload  # pylint: disable=protected-access

    async def initiate_upload(self, *args, **kwargs):
        session_uri = await original(self, *args, **kwargs)
        return session_uri.replace(
            f'{emulator.scheme}://{emulator.netloc}', PROXY_URL, 1,
        )

    monkeypatch.setattr(
        aio_storage.Storage, '_initiate_upload', initiate_upload,
    )

    clear_toxics()
    yield upload
    clear_toxics()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'toxic,attributes', [
        pytest.param('limit_data', {'bytes': 16 * 1024}, id='body-cut-off'),
        pytest.param('reset_peer', {'timeout': 0}, id='connection-reset'),
    ],
)
async def test_resumable_upload_recovers_from_connection_fault(
    bucket_name, creds, faulty_upload, toxic, attributes,
):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.bin'
    add_toxic(toxic, **attributes)

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        res = await storage.upload(
            bucket_name, object_name, DATA, force_resumable_upload=True,
        )

        # The first attempt hit the fault and the second one finished the
        # upload with exactly the original bytes. (Reads go straight to the
        # emulator, not through the proxy.)
        assert faulty_upload.delays == [1.0]
        assert await storage.download(bucket_name, res['name']) == DATA

        await storage.delete(bucket_name, res['name'])


@pytest.mark.asyncio
async def test_resumable_upload_gives_up_on_persistent_connection_fault(
    bucket_name, creds, faulty_upload,
):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.bin'
    faulty_upload.heal = False
    add_toxic('reset_peer', timeout=0)

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        with pytest.raises(ConnectionFailure):
            await storage.upload(
                bucket_name, object_name, DATA, force_resumable_upload=True,
            )

        assert faulty_upload.delays == [1.0, 2.0, 4.0, 8.0]
        assert len(faulty_upload.delays) == MAX_ATTEMPTS - 1

        # Nothing was committed.
        clear_toxics()
        with pytest.raises(ResponseError) as excinfo:
            await storage.download_metadata(bucket_name, object_name)
        assert status_of(excinfo.value) == 404
