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
    from gcloud.aio.datastore import Key
    from gcloud.aio.datastore import PathElement
    from gcloud.aio.datastore import GQLQuery

    ds = Datastore('my-gcloud-project', '/path/to/creds.json')
    key1 = Key('my-gcloud-project', [PathElement('Kind', 'entityname')])
    key2 = Key('my-gcloud-project', [PathElement('Kind', 'entityname2')])

    # batched lookups
    entities = await ds.lookup([key1, key2])

    # convenience functions for any datastore mutations
    await ds.insert(key1, {'a_boolean': True, 'meaning_of_life': 41})
    await ds.update(key1, {'a_boolean': True, 'meaning_of_life': 42})
    await ds.upsert(key1, {'animal': 'aardvark'})
    await ds.delete(key1)

    # or build your own mutation sequences with full transaction support
    transaction = await ds.beginTransaction()
    try:
        mutations = [
            ds.make_mutation(Operation.INSERT, key1, properties={'animal': 'sloth'}),
            ds.make_mutation(Operation.UPSERT, key1, properties={'animal': 'aardvark'}),
            ds.make_mutation(Operation.INSERT, key2, properties={'animal': 'aardvark'}),
        ]
        await ds.commit(transaction, mutations=[mutation])
    except Exception:
        await ds.rollback(transaction)

    # support for partial keys
    partial_key = Key('my-gcloud-project', [PathElement('Kind')])
    # and ID allocation or reservation
    allocated_keys = await ds.allocateIds([partial_key])
    await ds.reserveIds(allocated_keys)

    # query support
    query = GQLQuery('SELECT * FROM the_meaning_of_life WHERE answer = @answer',
                     named_bindings={'answer': 42})
    results = await ds.runQuery(query, session=s)

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-datastore.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-datastore/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-datastore.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-datastore/
