Releasing New Versions
======================

CircleCI manages the entire release process for us. Here's what you need to do:

Use poetry to update to the correct `semantic version`_, eg. via:

.. code-block:: console

    cd <project>/
    poetry version <major|minor|patch|prerelease>

Commit those changes to master and make sure CI is successful. Once it is, you
can create a release tag:

.. code-block:: console

    git tag taskqueue-1.2.3
    git push origin taskqueue-1.2.3

CircleCI will then create a `GitHub release`_. Release notes are auto-generated
from commit messages, but you'll need to double-check its been generated
properly and make any necessary changes to make it a bit more human-readable.
Once you've done that, you can click the "approve" button in CircleCI (which
should be linked in the workflow status for your commit).

Once you've approved the release notes, it will kick off CI jobs for releasing
said project and version to PyPI. Note that this will release both
``gcloud-aio-foo`` and ``gcloud-rest-foo``.

.. _GitHub release: https://github.com/talkiq/gcloud-aio/releases
.. _semantic version: http://semver.org/
