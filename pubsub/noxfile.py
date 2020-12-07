import json
import os

import nox


def require_creds(session):
    creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds:
        session.skip('credentials must be set via environment variable '
                     '$GOOGLE_APPLICATION_CREDENTIALS. Value not set; '
                     'skipping integration tests')

    try:
        with open(creds, 'r') as f:
            data = f.read()
            _ = json.loads(data)
            # not necessarily _valid_ creds, but that'd probably be too hard
            return
    except IOError:
        session.skip('credentials must be set via environment variable '
                     '$GOOGLE_APPLICATION_CREDENTIALS. Value does not point '
                     'to a file; skipping integration tests')
    except ValueError:
        session.skip('credentials must be set via environment variable '
                     '$GOOGLE_APPLICATION_CREDENTIALS. Value does not point '
                     'to a json-parseable file; skipping integration tests')

    session.skip('credentials must be set via environment '
                 'variable $GOOGLE_APPLICATION_CREDENTIALS. Value points to '
                 'an empty file; skipping integration tests')


@nox.session(python=['3.6', '3.7', '3.8', '3.9'], reuse_venv=True)
def unit_tests(session):
    session.install('future')
    session.install('pytest', 'pytest-cov', 'pytest-asyncio')
    session.install('-e', '.')

    session.run('py.test', '--quiet', '--cov=gcloud.aio.pubsub',
                '--cov=tests.unit', '--cov-append', '--cov-report=',
                os.path.join('tests', 'unit'), *session.posargs)


@nox.session(python=['3.9'], reuse_venv=True)
def integration_tests(session):
    require_creds(session)

    session.install('future')
    session.install('aiohttp', 'pytest', 'pytest-asyncio', 'pytest-mock')
    session.install('.')

    session.run('py.test', '--quiet', 'tests/integration')


@nox.session(python=['3.9'], reuse_venv=True)
def lint_setup_py(session):
    session.install('future')
    session.install('docutils', 'Pygments')
    session.run('python', 'setup.py', 'check', '--restructuredtext',
                '--strict')


@nox.session(python=['3'], reuse_venv=True)
def cover(session):
    session.install('future')
    session.install('coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing')
    session.run('coverage', 'erase')
