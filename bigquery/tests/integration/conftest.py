import json
import os
import time
import urllib.error
import urllib.request

import pytest

# When set, run against this emulator (eg. goccy/bigquery-emulator) rather than
# GCP.
EMULATOR_HOST = os.environ.get('BIGQUERY_EMULATOR_HOST')


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


def emulator_ensure(
        url: str, create_url: str, body: dict[str, object],
) -> None:
    """
    Create a resource unless it already exists, so that test runs can share an
    emulator. Emulators disagree on how to report conflicts, so check first.
    """
    try:
        emulator_request(url)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        emulator_request(create_url, body)


@pytest.fixture(scope='module')
def creds() -> str | None:
    if EMULATOR_HOST:
        return None

    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module', name='dataset')
def fixture_dataset(project: str) -> str:
    name = 'public_test'
    if EMULATOR_HOST:
        datasets = (
            f'http://{EMULATOR_HOST}/bigquery/v2/projects/{project}/datasets'
        )
        emulator_ensure(
            f'{datasets}/{name}', datasets,
            {'datasetReference': {'projectId': project, 'datasetId': name}},
        )
    return name


@pytest.fixture(scope='module')
def table(project: str, dataset: str) -> str:
    name = 'public_test'
    if EMULATOR_HOST:
        tables = (
            f'http://{EMULATOR_HOST}/bigquery/v2/projects/{project}'
            f'/datasets/{dataset}/tables'
        )
        emulator_ensure(
            f'{tables}/{name}', tables,
            {
                'tableReference': {
                    'projectId': project,
                    'datasetId': dataset,
                    'tableId': name,
                },
                # matches the real table
                'schema': {'fields': [
                    {'name': 'key', 'type': 'STRING', 'mode': 'REQUIRED'},
                    {'name': 'value', 'type': 'STRING', 'mode': 'REQUIRED'},
                ]},
            },
        )
    return name


@pytest.fixture(scope='module', name='project')
def fixture_project() -> str:
    return 'dialpad-oss'


@pytest.fixture(scope='module')
def export_bucket_name() -> str:
    return 'dialpad-oss-public-test'
