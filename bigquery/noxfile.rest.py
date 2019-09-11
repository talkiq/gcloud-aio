import os

import nox


LOCAL_DEPS = ('../auth/', )


@nox.session(python=['2.7', '3.5', '3.6', '3.7'], reuse_venv=True)
def unit_tests(session):
    session.install('future')
    session.install('pytest', 'pytest-cov', 'future')
    session.install('-e', *LOCAL_DEPS)
    session.install('-e', '.')

    session.run('py.test', '--quiet', '--cov=gcloud.rest', '--cov=tests.unit',
                '--cov-append', '--cov-report=', os.path.join('tests', 'unit'),
                *session.posargs)


@nox.session(python=['2.7', '3.7'], reuse_venv=True)
def integration_tests(session):
    session.install('future')
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        session.skip('Credentials must be set via environment variable.')

    session.install('pytest', 'pytest-cov', 'pytest-mock', 'future',)
    session.install('-e', *LOCAL_DEPS)
    session.install('-e', '.')

    session.run('py.test', '--quiet', '--cov=gcloud.rest',
                '--cov=tests.integration', '--cov-append', '--cov-report=',
                os.path.join('tests', 'integration'), *session.posargs)


@nox.session(python=['2.7', '3.7'], reuse_venv=True)
def lint_setup_py(session):
    session.install('future')
    session.install('docutils', 'Pygments', 'future')
    session.run('python', 'setup.py', 'check', '--restructuredtext',
                '--strict')


@nox.session(python=['3.7'], reuse_venv=True)
def cover(session):
    session.install('future')
    session.install('coverage', 'pytest-cov', 'future')

    session.run('coverage', 'report', '--show-missing')
    session.run('coverage', 'erase')
