import os

import nox


@nox.session(python=['2.7', '3.5', '3.6', '3.7'], reuse_venv=True)
def unit_tests(session):
    session.install('pytest', 'pytest-cov')
    session.install('-e', '.')

    session.run('py.test', '--quiet', '--cov=gcloud.rest', '--cov=tests.unit',
                '--cov-append', '--cov-report=', os.path.join('tests', 'unit'),
                *session.posargs)


# TODO: re-enable once we have some integration tests again
# @nox.session(python=['2.7', '3.7'], reuse_venv=True)
# def integration_tests(session):
#     if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
#         session.skip('Credentials must be set via environment variable.')

#     session.install('pytest', 'pytest-cov', 'pytest-mock')
#     session.install('.')

#     session.run('py.test', '--quiet', '--cov=gcloud.rest',
#                 '--cov=tests.integration', '--cov-append', '--cov-report=',
#                 os.path.join('tests', 'integration'), *session.posargs)


@nox.session(python=['2.7', '3.7'], reuse_venv=True)
def lint_setup_py(session):
    session.install('docutils', 'Pygments')
    session.run('python', 'setup.py', 'check', '--restructuredtext',
                '--strict')


@nox.session(python=['3.7'], reuse_venv=True)
def cover(session):
    session.install('coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing')
    session.run('coverage', 'erase')
