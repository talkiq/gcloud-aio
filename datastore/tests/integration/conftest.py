import json
import os
import time
import urllib.error
import urllib.request

import pytest

# When set, run against this emulator (eg. the Firestore emulator in Datastore
# mode) rather than GCP.
EMULATOR_HOST = os.environ.get('DATASTORE_EMULATOR_HOST')


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'real_gcp(reason): needs real GCP; skipped when using an emulator',
    )


def pytest_collection_modifyitems(items):
    if not EMULATOR_HOST:
        return

    for item in items:
        marker = item.get_closest_marker('real_gcp')
        if marker:
            reason = f"real GCP only: {marker.kwargs['reason']}"
            item.add_marker(pytest.mark.skip(reason=reason))


def emulator_request(url: str, body: dict[str, object] | None = None) -> None:
    """Send a request (a POST if it has a body) once the emulator is up."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url, data=data, headers={'Content-Type': 'application/json'},
    )
    deadline = time.monotonic() + 60
    while True:
        try:
            with urllib.request.urlopen(request, timeout=10):
                return
        except urllib.error.HTTPError:
            # an OSError too, but means the emulator is up
            raise
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


@pytest.fixture(scope='session', autouse=True)
def emulator() -> None:
    if EMULATOR_HOST:
        emulator_request(f'http://{EMULATOR_HOST}/')


@pytest.fixture(scope='module')
def creds() -> str | None:
    if EMULATOR_HOST:
        return None

    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')
def kind() -> str:
    return 'public_test'


@pytest.fixture(scope='module')
def project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def export_bucket_name() -> str:
    return 'dialpad-oss-public-test'
