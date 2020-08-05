(Asyncio OR Threadsafe) Python Client for Google Cloud BigQuery
===============================================================

    This is a shared codebase for ``gcloud-aio-bigquery`` and
    ``gcloud-rest-bigquery``

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-bigquery

Usage
-----

We're still working on documentation -- for now, you can use the `smoke test`_
as an example.

Emulators
~~~~~~~~~

For testing purposes, you may want to use ``gcloud-aio-bigquery`` along with a
local emulator. Setting the ``$BIGQUERY_EMULATOR_HOST`` environment variable
to the address of your emulator should be enough to do the trick.

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-rest/blob/master/.github/CONTRIBUTING.rst
.. _smoke test: https://github.com/talkiq/gcloud-rest/blob/master/bigquery/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-bigquery.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-bigquery)
    :target: https://pypi.org/project/gcloud-aio-bigquery/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-bigquery.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-bigquery)
    :target: https://pypi.org/project/gcloud-aio-bigquery/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-bigquery.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-bigquery)
    :target: https://pypi.org/project/gcloud-rest-bigquery/
