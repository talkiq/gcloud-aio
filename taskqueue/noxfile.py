import os

import nox


LOCAL_DEPS = ('../auth/', )


@nox.session(python=['3.6', '3.7'], reuse_venv=True)
def unit_tests(session):
    session.install('pytest', 'pytest-cov', *LOCAL_DEPS)
    session.install('-e', '.')

    session.run('py.test', '--quiet', '--cov=gcloud.aio.taskqueue',
                '--cov=tests.unit', '--cov-append', '--cov-report=',
                os.path.join('tests', 'unit'), *session.posargs)


@nox.session(python=['3.7'], reuse_venv=True)
def integration_tests(session):
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    session.install('aiohttp', 'pytest', 'pytest-asyncio', 'pytest-mock',
                    *LOCAL_DEPS)
    session.install('.')

    session.run('py.test', '--quiet', 'tests/integration')


@nox.session(python=['3.7'], reuse_venv=True)
def lint_setup_py(session):
    session.install('docutils', 'Pygments')
    session.run('python', 'setup.py', 'check', '--restructuredtext',
                '--strict')


@nox.session(python=['3.7'], reuse_venv=True)
def cover(session):
    session.install('coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing')
    session.run('coverage', 'erase')
