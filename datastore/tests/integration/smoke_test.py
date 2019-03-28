import uuid

import aiohttp
import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import GQLQuery
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value


@pytest.mark.asyncio  # type: ignore
async def test_item_lifecycle(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        allocatedKeys = await ds.allocateIds([key], session=s)
        assert len(allocatedKeys) == 1
        key.path[-1].id = allocatedKeys[0].path[-1].id
        assert key == allocatedKeys[0]

        await ds.reserveIds(allocatedKeys, session=s)

        props_insert = {'is_this_bad_data': True}
        await ds.insert(allocatedKeys[0], props_insert, session=s)
        actual = await ds.lookup([allocatedKeys[0]], session=s)
        assert actual['found'][0].entity.properties == props_insert

        props_update = {'animal': 'aardvark', 'overwrote_bad_data': True}
        await ds.update(allocatedKeys[0], props_update, session=s)
        actual = await ds.lookup([allocatedKeys[0]], session=s)
        assert actual['found'][0].entity.properties == props_update

        props_upsert = {'meaning_of_life': 42}
        await ds.upsert(allocatedKeys[0], props_upsert, session=s)
        actual = await ds.lookup([allocatedKeys[0]], session=s)
        assert actual['found'][0].entity.properties == props_upsert

        await ds.delete(allocatedKeys[0], session=s)
        actual = await ds.lookup([allocatedKeys[0]], session=s)
        assert len(actual['missing']) == 1


@pytest.mark.asyncio  # type: ignore
async def test_transaction(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind, name=f'test_record_{uuid.uuid4()}')])

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        actual = await ds.lookup([key], transaction=transaction, session=s)
        assert len(actual['missing']) == 1

        mutations = [
            ds.make_mutation(Operation.INSERT, key,
                             properties={'animal': 'three-toed sloth'}),
            ds.make_mutation(Operation.UPDATE, key,
                             properties={'animal': 'aardvark'}),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        actual = await ds.lookup([key], session=s)
        assert actual['found'][0].entity.properties == {'animal': 'aardvark'}


@pytest.mark.asyncio  # type: ignore
async def test_rollback(creds: str, project: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        await ds.rollback(transaction, session=s)


@pytest.mark.asyncio  # type: ignore
@pytest.mark.xfail(strict=False)  # type: ignore
async def test_query(creds: str, kind: str, project: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        property_filter = PropertyFilter(
            prop='value', operator=PropertyFilterOperator.EQUAL,
            value=Value(42))
        query = Query(kind=kind, query_filter=Filter(property_filter))

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(Operation.INSERT,
                             Key(project, [PathElement(kind)]),
                             properties={'value': 42}),
            ds.make_mutation(Operation.INSERT,
                             Key(project, [PathElement(kind)]),
                             properties={'value': 42}),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 2


@pytest.mark.asyncio  # type: ignore
@pytest.mark.xfail(strict=False)  # type: ignore
async def test_gql_query(creds: str, kind: str, project: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        query = GQLQuery(f'SELECT * FROM {kind} WHERE value = @value',
                         named_bindings={'value': 42})

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(Operation.INSERT,
                             Key(project, [PathElement(kind)]),
                             properties={'value': 42}),
            ds.make_mutation(Operation.INSERT,
                             Key(project, [PathElement(kind)]),
                             properties={'value': 42}),
            ds.make_mutation(Operation.INSERT,
                             Key(project, [PathElement(kind)]),
                             properties={'value': 42}),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 3
