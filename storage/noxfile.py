# pylint: disable=import-self,no-member
import os
import nox


LOCAL_DEPS = ('../auth/', )


@nox.session(python=['3.6', '3.7'])
def unit_tests(session):
    session.install('pytest', 'pytest-cov', *LOCAL_DEPS)
    session.install('-e', '.')

    session.run(
        'py.test',
        '--quiet',
        '--cov=gcloud.aio.storage',
        '--cov=tests.unit',
        '--cov-append',
        '--cov-report=',
        os.path.join('tests', 'unit'),
        *session.posargs)


@nox.session(python=['3.7'])
def integration_tests(session):
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip(
            'Credentials must be set via the environment variable "GOOGLE_APPLICATION_CREDENTIALS".')
    if not os.environ.get('BUCKET_NAME', ''):
        session.skip(
            'Gcloud bucket name must be set via the environment variable: "BUCKET_NAME".')
    if not os.environ.get('GCLOUD_PROJECT', ''):
        session.skip(
            'Gcloud project id must be set via the environment variable: "GCLOUD_PROJECT".')

    session.install('aiohttp', 'pytest', 'pytest-asyncio', *LOCAL_DEPS)
    session.install('.')

    session.run('py.test', '--quiet', 'tests/integration')


@nox.session(python=['3.7'])
def lint_setup_py(session):
    session.install('docutils', 'Pygments')
    session.run(
        'python',
        'setup.py',
        'check',
        '--restructuredtext',
        '--strict')


@nox.session(python=['3.7'])
def cover(session):
    session.install('codecov', 'coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing')
    session.run('codecov')
    session.run('coverage', 'erase')
