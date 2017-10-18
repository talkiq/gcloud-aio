# pylint: disable=import-self,no-member
import nox


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
