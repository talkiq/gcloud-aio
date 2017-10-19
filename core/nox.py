# pylint: disable=import-self,no-member
import os

import nox


@nox.session
@nox.parametrize('python_version', ['3.6'])
def unit_tests(session, python_version):
    session.interpreter = 'python{}'.format(python_version)
    session.virtualenv_dirname = 'unit-' + python_version

    session.install('mock', 'pytest', 'pytest-cov')
    session.install('-e', '.')

    session.run(
        'py.test',
        '--quiet',
        '--cov=gcloud.aio.core',
        '--cov=tests.unit',
        '--cov-append',
        '--cov-report=',
        '--cov-fail-under=40',
        os.path.join('tests', 'unit'),
        *session.posargs)


@nox.session
@nox.parametrize('python_version', ['3.6'])
def lint_setup_py(session, python_version):
    session.interpreter = 'python{}'.format(python_version)
    session.virtualenv_dirname = 'setup'

    session.install('docutils', 'Pygments')
    session.run(
        'python',
        'setup.py',
        'check',
        '--restructuredtext',
        '--strict')


@nox.session
@nox.parametrize('python_version', ['3.6'])
def cover(session, python_version):
    session.interpreter = 'python{}'.format(python_version)
    session.virtualenv_dirname = 'cover'

    session.install('codecov', 'coverage', 'pytest-cov')

    session.run('coverage', 'report', '--show-missing', '--fail-under=40')
    session.run('codecov')
    session.run('coverage', 'erase')
