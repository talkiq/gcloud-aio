Asyncio Python Client for Google Cloud Datastore
================================================

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-datastore

Usage
-----

We're still working on documentation; for now, this should help get you
started:

.. code-block:: python

    from gcloud.aio.datastore import Datastore

    datastore = Datastore('my-gcloud-project', '/path/to/creds.json')

    await datastore.insert('Kind', 'name', {'prop0': 41, 'prop1': True})
    await datastore.update('Kind', 'name', {'prop0': 42, 'prop1': True})
    await datastore.upsert('Kind', 'name', {'prop2': 'aardvark'})

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-datastore.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-datastore/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-datastore.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-datastore/
