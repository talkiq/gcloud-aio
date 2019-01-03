Releasing New Versions
======================

CircleCI manages the entire release process for us. Here's what you need to do:

Make sure the ``setup.py`` for the project you're releasing gets a version
bump. `Semantic versioning`_ (``x.y.z``) is great.

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

.. _GitHub release: https://github.com/talkiq/gcloud-aio/releases
.. _Semantic versioning: http://semver.org/
