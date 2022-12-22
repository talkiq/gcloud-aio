"""
This library implements various methods for working with the Google Datastore
APIs.

## Installation

```console
$ pip install --upgrade gcloud-aio-datastore
```

## Usage

We're still working on documentation; for now, this should help get you
started:

```python
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Direction
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import GQLQuery
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import PropertyOrder
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value

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
        ds.make_mutation(Operation.INSERT, key1,
                         properties={'animal': 'sloth'}),
        ds.make_mutation(Operation.UPSERT, key1,
                         properties={'animal': 'aardvark'}),
        ds.make_mutation(Operation.INSERT, key2,
                         properties={'animal': 'aardvark'}),
    ]
    await ds.commit(transaction, mutations=mutations)
except Exception:
    await ds.rollback(transaction)

# support for partial keys
partial_key = Key('my-gcloud-project', [PathElement('Kind')])
# and ID allocation or reservation
allocated_keys = await ds.allocateIds([partial_key])
await ds.reserveIds(allocated_keys)

# query support
property_filter = PropertyFilter(prop='answer',
                                 operator=PropertyFilterOperator.EQUAL,
                                 value=Value(42))
property_order = PropertyOrder(prop='length',
                               direction=Direction.DESCENDING)
query = Query(kind='the_meaning_of_life',
              query_filter=Filter(property_filter),
              order=property_order)
results = await ds.runQuery(query, session=s)

# alternatively, query support using GQL
gql_query = GQLQuery('SELECT * FROM meaning_of_life WHERE answer = @answer',
                     named_bindings={'answer': 42})
results = await ds.runQuery(gql_query, session=s)

# close the HTTP session
# Note that other options include:
# * providing your own session: `Datastore(.., session=session)`
# * using a context manager: `async with Datastore(..) as ds:`
await ds.close()
```

## Custom Subclasses

`gcloud-aio-datastore` provides class interfaces mirroring all official Google
API types, ie. `Key` and `PathElement`, `Entity` and `EntityResult`,
`QueryResultBatch`, and `Value`. These types will be returned from arbitrary
Datastore operations, for example `Datastore.allocateIds(...)` will return a
list of `Key` entities.

For advanced usage, all of these datatypes may be overloaded. A common use-case
may be to deserialize entities into more specific classes. For example, given a
custom entity class such as:

```python
class MyEntityKind(gcloud.aio.datastore.Entity):
    def __init__(self, key, properties = None) -> None:
        self.key = key
        self.is_an_aardvark = (properties or {}).get('aardvark', False)

    def __repr__(self):
        return "I'm an aardvark!" if self.is_an_aardvark else "Sorry, nope"
```

We can then configure `gcloud-aio-datastore` to serialize/deserialize from this
custom entity class with:

```python
class MyCustomDatastore(gcloud.aio.datastore.Datastore):
    entity_result_kind.entity_kind = MyEntityKind
```

The full list of classes which may be overridden in this way is:

```python
class MyVeryCustomDatastore(gcloud.aio.datastore.Datastore):
    datastore_operation_kind = DatastoreOperation
    entity_result_kind = EntityResult
    entity_result_kind.entity_kind = Entity
    entity_result_kind.entity_kind.key_kind = Key
    key_kind = Key
    key_kind.path_element_kind = PathElement
    mutation_result_kind = MutationResult
    mutation_result_kind.key_kind = Key
    query_result_batch_kind = QueryResultBatch
    query_result_batch_kind.entity_result_kind = EntityResult
    value_kind = Value
    value_kind.key_kind = Key

class MyVeryCustomQuery(gcloud.aio.datastore.Query):
    value_kind = Value

class MyVeryCustomGQLQuery(gcloud.aio.datastore.GQLQuery):
    value_kind = Value
```

You can then drop-in the `MyVeryCustomDatastore` class anywhere where you
previously used `Datastore` and do the same for `Query` and `GQLQuery`.

To override any sub-key, you'll need to override any parents which use it. For
example, if you want to use a custom Key kind and be able to use queries with
it, you will need to implement your own `Value`, `Query`, and `GQLQuery`
classes and wire them up to the rest of the custom classes:

```python
class MyKey(gcloud.aio.datastore.Key):
    pass

class MyValue(gcloud.aio.datastore.Value):
    key_kind = MyKey

class MyEntity(gcloud.aio.datastore.Entity):
    key_kind = MyKey
    value_kind = MyValue

class MyEntityResult(gcloud.aio.datastore.EntityResult):
    entity_kind = MyEntity

class MyQueryResultBatch(gcloud.aio.datastore.QueryResultBatch):
    entity_result_kind = MyEntityResult

class MyDatastore(gcloud.aio.datastore.Datastore):
    key_kind = MyKey
    entity_result_kind = MyEntityResult
    query_result_batch = MyQueryResultBatch
    value_kind = MyValue

class MyQuery(gcloud.aio.datastore.Query):
    value_kind = MyValue

class MyGQLQuery(gcloud.aio.datastore.GQLQuery):
    value_kind = MyValue
```
"""
from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-datastore').version

from gcloud.aio.datastore.constants import CompositeFilterOperator
from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Direction
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import MoreResultsType
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.constants import PropertyFilterOperator
from gcloud.aio.datastore.constants import ResultType
from gcloud.aio.datastore.datastore import Datastore
from gcloud.aio.datastore.datastore import SCOPES
from gcloud.aio.datastore.datastore_operation import DatastoreOperation
from gcloud.aio.datastore.entity import Entity
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.filter import CompositeFilter
from gcloud.aio.datastore.filter import Filter
from gcloud.aio.datastore.filter import PropertyFilter
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.key import PathElement
from gcloud.aio.datastore.lat_lng import LatLng
from gcloud.aio.datastore.mutation import MutationResult
from gcloud.aio.datastore.projection import Projection
from gcloud.aio.datastore.property_order import PropertyOrder
from gcloud.aio.datastore.query import GQLCursor
from gcloud.aio.datastore.query import GQLQuery
from gcloud.aio.datastore.query import Query
from gcloud.aio.datastore.query import QueryResultBatch
from gcloud.aio.datastore.value import Value


__all__ = [
    'CompositeFilter',
    'CompositeFilterOperator',
    'Consistency',
    'Datastore',
    'DatastoreOperation',
    'Direction',
    'Entity',
    'EntityResult',
    'Filter',
    'GQLCursor',
    'GQLQuery',
    'Key',
    'LatLng',
    'Mode',
    'MoreResultsType',
    'MutationResult',
    'Operation',
    'PathElement',
    'Projection',
    'PropertyFilter',
    'PropertyFilterOperator',
    'PropertyOrder',
    'Query',
    'QueryResultBatch',
    'ResultType',
    'SCOPES',
    'Value',
    '__version__',
]
