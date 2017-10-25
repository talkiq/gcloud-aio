Releasing New Versions
======================

CircleCI manages the entire release process for us. Here's what you need to do:

Make sure the ``setup.py`` for the project you're releasing gets a version
bump. `Semantic versioning`_ (``x.y.z``) is great.

Make sure you also update the relevant ``requirements.txt`` files, if need be.

Commit those changes to master and make sure CI is successful. Once it is, you
can create a release tag:

.. code-block:: console

    git tag taskqueue-1.2.3
    git push --tags

The tag format is "``project``-x.y.z"; that will kick off CI jobs for releasing
said project and version to PyPI.

CircleCI will also create a `GitHub release`_. Release notes are auto-generated
from commit messages, but you may want to check the new release and clean the
changelog up, just in case.

Base Project
------------

The ``gcloud-aio`` meta-project is a bit special in this regard, since it isn't
really tied to any features in and of itself. We want to promote users to
install and use the sub-projects rather than itself, but having a single
"install everything" project is still a good idea (and mirrors the official
``google-cloud`` project structure).

Our current process it to do a meta-project release whenever a sub-project gets
a *major* version bump.

To release a new meta-project, update the global ``setup.py`` and run:

.. code-block:: console

    rm -rf dist/
    python setup.py sdist bdist_wheel
    twine upload dist/*

.. _GitHub release: https://github.com/talkiq/gcloud-aio/releases
.. _Semantic versioning: http://semver.org/
