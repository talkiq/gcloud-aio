Auth Helpers for Asyncio Google Cloud Library
=============================================

This library is not meant to be a standalone project, rather it is used by
various ``gcloud-aio-*`` packages.

This library implements a ``Token`` class, which is used for authorizing
against Google Cloud. The other ``gcloud-aio-*`` package components accept a
``Token`` instance as an argument; you can define a single token for all of
these components or define one for each. Each component corresponds to a given
Google Cloud service and each service requires "`scopes`_".

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-auth

Usage
-----

We're still working on documentation -- for now, you can use the `smoke test`_
as an example.

.. _scopes: https://developers.google.com/identity/protocols/googlescopes
.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/auth/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-auth.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-auth/
