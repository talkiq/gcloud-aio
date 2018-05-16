# pylint: disable=import-self,no-member
import os

import nox


@nox.session
@nox.parametrize('python_version', ['3.6', '3.7'])
def unit_tests(session, python_version):
    session.interpreter = f'python{python_version}'
    session.virtualenv_dirname = f'unit-{python_version}'

    session.install('pytest', 'pytest-cov')
    session.install('-e', '.')

    session.run(
        'py.test',
        '--quiet',
        '--cov=gcloud.aio.pubsub',
        '--cov=tests.unit',
        '--cov-append',
        '--cov-report=',
        os.path.join('tests', 'unit'),
        *session.posargs)


@nox.session
@nox.parametrize('python_version', ['3.6', '3.7'])
def integration_tests(session, python_version):
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    session.interpreter = f'python{python_version}'
    session.virtualenv_dirname = f'integration-{python_version}'

    session.install('pytest')
    session.install('.')

    session.run('py.test', '--quiet', 'tests/integration')


@nox.session
@nox.parametrize('python_version', ['3.7'])
def lint_setup_py(session, python_version):
    session.interpreter = f'python{python_version}'
    session.virtualenv_dirname = 'setup'

    session.install('docutils', 'Pygments')
    session.run(
        'python',
        'setup.py',
        'check',
        '--restructuredtext',
        '--strict')


@nox.session
@nox.parametrize('python_version', ['3.7'])
def cover(session, python_version):
    session.interpreter = f'python{python_version}'
    session.virtualenv_dirname = 'cover'

    session.install('codecov', 'coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing')
    session.run('codecov')
    session.run('coverage', 'erase')
