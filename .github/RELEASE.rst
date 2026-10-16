Releasing New Versions
======================

GitHub Actions manages the entire release process for us (see
``.github/workflows/release.yml``). Here's what you need to do:

Use poetry to update to the correct `semantic version`_, eg. via:

.. code-block:: console

    cd <project>/
    poetry version <major|minor|patch|prerelease>

Commit those changes to master and make sure CI is successful. Once it is, you
can create a release tag:

.. code-block:: console

    git tag taskqueue-1.2.3
    git push origin taskqueue-1.2.3

The ``release`` workflow will wait for CircleCI to pass on that commit, build
the packages, and then create a `GitHub release`_. Release notes are
auto-generated from commit messages, but you'll need to double-check its been
generated properly and make any necessary changes to make it a bit more
human-readable. Once you've done that, approve the pending deployment to the
``release`` environment from the workflow run (any member of
``@talkiq/engineering`` can approve).

Once approved, the workflow publishes said project and version to PyPI via
trusted publishing. Note that this will release both ``gcloud-aio-foo`` and
``gcloud-rest-foo``.

The GitHub environments and PyPI trusted publishers this relies on are
configured by ``bin/setup-ci github`` and ``bin/setup-ci pypi``.

.. _GitHub release: https://github.com/talkiq/gcloud-aio/releases
.. _semantic version: http://semver.org/
