import io
import os
import json
from pathlib import Path

import gcloud.aio.auth.token as token
import pytest


@pytest.mark.asyncio
async def test_service_as_io():
    # pylint: disable=line-too-long
    service_data = {
        'type': 'service_account',
        'project_id': 'random-project-123',
        'private_key_id': '399asdfsdf92923k32423a9f9sdf',
        'private_key': '-----BEGIN PRIVATE KEY-----\nABCDF012923949394239492349234923==\n-----END PRIVATE KEY-----\n',
        'client_email': 'gcloud-aio-test@random-project-123.iam.gserviceaccount.com',
        'client_id': '2384283429349234293',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/gcloud-aio%40random-project-123.iam.gserviceaccount.com'
    }

    # io.StringIO does not like str inputs in python2. So in `py3to2` step in CI
    # runs `future-fstrings-show` redefines str literals to unicode, which turns
    # this seemingly noop operation to allow the literal string to get converted
    # to unicode.
    service_file = io.StringIO('{}'.format(json.dumps(service_data)))
    t = token.Token(service_file=service_file,
                    scopes=['https://google.com/random-scope'])

    assert t.token_type == token.Type.SERVICE_ACCOUNT
    assert t.token_uri == 'https://oauth2.googleapis.com/token'
    assert await t.get_project() == 'random-project-123'


@pytest.fixture
def chdir(tmp_path):
    old_dir = os.curdir
    os.chdir(str(tmp_path))
    try:
        yield
    finally:
        os.chdir(old_dir)


@pytest.fixture
def clean_environ():
    old_environ = os.environ.copy()
    os.environ.clear()
    try:
        yield
    finally:
        os.environ.update(old_environ)


@pytest.mark.parametrize('given, expected', [
    ('{"name": "aragorn"}', {'name': 'aragorn'}),
    (io.StringIO('{"name": "aragorn"}'), {'name': 'aragorn'}),
    ('key.json', {'hello': 'world'}),
    (Path('key.json'), {'hello': 'world'}),
])
def test_get_service_data__explicit(tmp_path: Path, chdir, given, expected):
    (tmp_path / 'key.json').write_text('{"hello": "world"}')
    assert token.get_service_data(given) == expected


@pytest.mark.parametrize('given, expected', [
    ('something', json.JSONDecodeError),
    (io.StringIO('something'), json.JSONDecodeError),
    (Path('something'), FileNotFoundError),
])
def test_get_service_data__explicit__raise(given, expected):
    with pytest.raises(expected):
        token.get_service_data(given)


@pytest.mark.parametrize('given, expected', [
    ({'GOOGLE_APPLICATION_CREDENTIALS': 'key.json'}, {'hello': 'world'}),
    ({'GOOGLE_APPLICATION_CREDENTIALS': '{"name": "aragorn"}'}, {'name': 'aragorn'}),
    ({'CLOUDSDK_CONFIG': '.'}, {'hi': 'mark'}),
    ({'CLOUDSDK_CONFIG': '{"name": "aragorn"}'}, {'name': 'aragorn'}),
])
def test_get_service_data__explicit_env_var(
    tmp_path: Path, chdir, clean_environ, given, expected,
):
    (tmp_path / 'key.json').write_text('{"hello": "world"}')
    (tmp_path / 'application_default_credentials.json').write_text('{"hi": "mark"}')
    os.environ.update(given)
    assert token.get_service_data(None) == expected


def test_get_service_data__explicit_env_var__raises(clean_environ):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'garbage'
    with pytest.raises(json.JSONDecodeError):
        token.get_service_data(None)


SDK_CONFIG = Path.home() / '.config' / 'gcloud' / 'application_default_credentials.json'


@pytest.mark.skipif(not SDK_CONFIG.exists(), reason='no default credentials installed')
def test_get_service_data__implicit_sdk_config(clean_environ):
    assert 'client_id' in token.get_service_data(None)
