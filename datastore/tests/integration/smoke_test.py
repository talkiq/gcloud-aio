import datetime
import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.datastore import Array
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import GQLCursor
from gcloud.aio.datastore import GQLQuery
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import Projection
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value
from gcloud.aio.datastore.transaction_options import ReadWrite
from gcloud.aio.datastore.transaction_options import TransactionOptions
from gcloud.aio.storage import Storage  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
    from time import sleep
else:
    from aiohttp import ClientSession as Session
    from asyncio import sleep


@pytest.mark.asyncio
async def test_item_lifecycle(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with Session() as s:
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


@pytest.mark.asyncio
async def test_mutation_result(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        insert_result = await ds.insert(key, {'value': 12})
        assert len(insert_result['mutationResults']) == 1
        saved_key = insert_result['mutationResults'][0].key
        assert saved_key is not None

        update_result = await ds.update(saved_key, {'value': 83})
        assert len(update_result['mutationResults']) == 1
        assert update_result['mutationResults'][0].key is None

        delete_result = await ds.delete(saved_key)
        assert len(delete_result['mutationResults']) == 1
        assert delete_result['mutationResults'][0].key is None


@pytest.mark.asyncio
async def test_insert_value_object(
    creds: str, kind: str, project: str,
) -> None:
    key = Key(project, [PathElement(kind)])

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)
        properties = {'value': Value(30, exclude_from_indexes=True)}
        insert_result = await ds.insert(key, properties)
        assert len(insert_result['mutationResults']) == 1


@pytest.mark.asyncio
async def test_start_transaction_on_lookup(creds: str,
                                           kind: str,
                                           project: str) -> None:
    key = Key(project, [PathElement(kind, name=f'test_record_{uuid.uuid4()}')])

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        options = TransactionOptions(ReadWrite())
        result = await ds.lookup([key], newTransaction=options, session=s)
        assert 'transaction' in result and result['transaction'] is not None
        assert len(result['missing']) == 1

        mutations = [
            ds.make_mutation(
                Operation.INSERT, key,
                properties={'animal': 'three-toed sloth'},
            ),
            ds.make_mutation(
                Operation.UPDATE, key,
                properties={'animal': 'aardvark'},
            ),
        ]
        await ds.commit(
            mutations,
            transaction=result['transaction'],
            session=s)

        actual = await ds.lookup([key], session=s)
        assert actual['found'][0].entity.properties == {'animal': 'aardvark'}


@pytest.mark.asyncio
async def test_transaction(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind, name=f'test_record_{uuid.uuid4()}')])

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        actual = await ds.lookup([key], transaction=transaction, session=s)
        assert len(actual['missing']) == 1

        mutations = [
            ds.make_mutation(
                Operation.INSERT, key,
                properties={'animal': 'three-toed sloth'},
            ),
            ds.make_mutation(
                Operation.UPDATE, key,
                properties={'animal': 'aardvark'},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        actual = await ds.lookup([key], session=s)
        assert actual['found'][0].entity.properties == {'animal': 'aardvark'}


@pytest.mark.asyncio
async def test_rollback(creds: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        await ds.rollback(transaction, session=s)


@pytest.mark.asyncio
async def test_query_with_key_projection(
    creds: str, kind: str,
    project: str,
) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)
        # setup test data
        await ds.insert(Key(project, [PathElement(kind)]), {'value': 30}, s)
        property_filter = PropertyFilter(
            prop='value', operator=PropertyFilterOperator.EQUAL,
            value=Value(30),
        )
        projection = [Projection.from_repr({'property': {'name': '__key__'}})]

        query = Query(
            kind=kind, query_filter=Filter(property_filter), limit=1,
            projection=projection,
        )
        result = await ds.runQuery(query, session=s)
        assert result.entity_results[0].entity.properties == {}
        assert result.entity_result_type.value == 'KEY_ONLY'
        # clean up test data
        await ds.delete(result.entity_results[0].entity.key, s)


@pytest.mark.asyncio
async def test_query_with_value_projection(
    creds: str, kind: str,
    project: str,
) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)
        # setup test data
        await ds.insert(Key(project, [PathElement(kind)]), {'value': 30}, s)
        projection = [Projection.from_repr({'property': {'name': 'value'}})]

        query = Query(
            kind=kind, limit=1,
            projection=projection,
        )
        result = await ds.runQuery(query, session=s)
        assert result.entity_result_type.value == 'PROJECTION'
        # clean up test data
        await ds.delete(result.entity_results[0].entity.key, s)


@pytest.mark.asyncio
async def test_query_with_distinct_on(
    creds: str, kind: str,
    project: str,
) -> None:
    keys1 = [Key(project, [PathElement(kind)]) for i in range(3)]
    keys2 = [Key(project, [PathElement(kind)]) for i in range(3)]
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        # setup test data
        allocatedKeys1 = await ds.allocateIds(keys1, session=s)
        allocatedKeys2 = await ds.allocateIds(keys2, session=s)
        for key1 in allocatedKeys1:
            await ds.insert(key1, {'dist_value': 11}, s)
        for key2 in allocatedKeys2:
            await ds.insert(key2, {'dist_value': 22}, s)
        query = Query(kind=kind, limit=10, distinct_on=['dist_value'])
        result = await ds.runQuery(query, session=s)
        assert len(result.entity_results) == 2
        # clean up test data
        for key1 in allocatedKeys1:
            await ds.delete(key1, s)
        for key2 in allocatedKeys2:
            await ds.delete(key2, s)


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_query(creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        property_filter = PropertyFilter(
            prop='value', operator=PropertyFilterOperator.EQUAL,
            value=Value(42),
        )
        query = Query(kind=kind, query_filter=Filter(property_filter))

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 42},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 42},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 2


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_query_with_in_filter(
        creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        property_filter = PropertyFilter(
            prop='value', operator=PropertyFilterOperator.IN,
            value=Array([Value(99), Value(100)]),
        )
        query = Query(kind=kind, query_filter=Filter(property_filter))

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 99},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 100},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 101},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 2


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_query_with_not_in_filter(
        creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        property_filter = PropertyFilter(
            prop='value', operator=PropertyFilterOperator.NOT_IN,
            value=Array([Value(99), Value(100), Value(30), Value(42)]),
        )
        query = Query(kind=kind, query_filter=Filter(property_filter))

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 99},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 100},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 999},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 1


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_gql_query(creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        query = GQLQuery(
            f'SELECT * FROM {kind} WHERE value = @value',
            named_bindings={'value': 42},
        )

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 42},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 42},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 42},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 3


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_gql_query_with_in_filter(
        creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        query = GQLQuery(
            f'SELECT * FROM {kind} WHERE value IN @values',
            named_bindings={'values': Array([Value(99), Value(100)])},
        )

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 99},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 100},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 101},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 2


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_gql_query_with_not_in_filter(
        creds: str, kind: str, project: str) -> None:
    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        query = GQLQuery(
            f'SELECT * FROM {kind} WHERE value NOT IN @values',
            named_bindings={'values': Array(
                [Value(30), Value(42), Value(99), Value(100)])},
        )

        before = await ds.runQuery(query, session=s)
        num_results = len(before.entity_results)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 99},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 100},
            ),
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties={'value': 999},
            ),
        ]
        await ds.commit(mutations, transaction=transaction, session=s)

        after = await ds.runQuery(query, session=s)
        assert len(after.entity_results) == num_results + 1


@pytest.mark.asyncio
@pytest.mark.xfail(strict=False)
async def test_gql_query_pagination(
        creds: str, kind: str, project: str,
) -> None:
    async with Session() as s:
        query_string = (
            f'SELECT __key__ FROM {kind}'
            'WHERE value = @value LIMIT @limit OFFSET @offset'
        )
        named_bindings = {'value': 42, 'limit': 2 ** 31 - 1, 'offset': 0}

        ds = Datastore(project=project, service_file=creds, session=s)

        before = await ds.runQuery(
            GQLQuery(query_string, named_bindings=named_bindings), session=s,
        )

        insertion_count = 8
        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(
                Operation.INSERT,
                Key(project, [PathElement(kind)]),
                properties=named_bindings,
            ),
        ] * insertion_count
        await ds.commit(mutations, transaction=transaction, session=s)

        page_size = 5
        named_bindings['limit'] = page_size
        named_bindings['offset'] = GQLCursor(before.end_cursor)
        first_page = await ds.runQuery(
            GQLQuery(query_string, named_bindings=named_bindings), session=s,
        )
        assert (len(first_page.entity_results)) == page_size

        named_bindings['offset'] = GQLCursor(first_page.end_cursor)
        second_page = await ds.runQuery(
            GQLQuery(query_string, named_bindings=named_bindings), session=s,
        )
        assert len(second_page.entity_results) == insertion_count - page_size


@pytest.mark.asyncio
async def test_datastore_export(
    creds: str, project: str,
    export_bucket_name: str,
):
    # N.B. when modifying this test, please also see `test_table_load_copy` in
    # `gcloud-aio-bigquery`.
    kind = 'PublicTestDatastoreExportModel'

    rand_uuid = str(uuid.uuid4())

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        await ds.insert(
            Key(project, [PathElement(kind)]),
            properties={'rand_str': rand_uuid},
        )

        operation = await ds.export(export_bucket_name, kinds=[kind])

        count = 0
        while (
            count < 10
            and operation
            and operation.metadata['common']['state'] == 'PROCESSING'
        ):
            await sleep(10)
            operation = await ds.get_datastore_operation(operation.name)
            count += 1

        assert operation.metadata['common']['state'] == 'SUCCESSFUL'

        prefix_len = len(f'gs://{export_bucket_name}/')
        export_path = operation.metadata['outputUrlPrefix'][prefix_len:]

        storage = Storage(service_file=creds, session=s)
        files = await storage.list_objects(
            export_bucket_name,
            params={'prefix': export_path},
        )
        for file in files['items']:
            await storage.delete(export_bucket_name, file['name'])


@pytest.mark.asyncio
async def test_lookup_with_read_time(
        creds: str, kind: str, project: str) -> None:
    key = Key(
        project, [
            PathElement(
                kind, name=f'test_read_time_{uuid.uuid4()}')])

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        # Test 1: Insert and read entity without readTime
        time_before_insert = datetime.datetime.utcnow()
        await ds.insert(key, {'value': 'test_data', 'timestamp': 'after'}, session=s)

        result = await ds.lookup([key], session=s)
        assert len(result['found']) == 1
        assert result['found'][0].entity.properties['value'] == 'test_data'
        assert result['readTime'] is not None

        # Test 2: Look up entity ver closest before current time
        current_time = datetime.datetime.utcnow()
        result_with_datetime = await ds.lookup([key], read_time=current_time, session=s)
        assert len(result_with_datetime.get('found', [])) == 1
        assert 'readTime' in result_with_datetime

        # Test 3: Look up entity before insertion timestamp; should not find
        # anything
        past_time = time_before_insert - datetime.timedelta(seconds=10)
        result_past = await ds.lookup([key], read_time=past_time, session=s)
        assert len(result_past.get('found', [])) == 0
        assert len(result_past.get('missing', [])) == 1

        # cleanup
        await ds.delete(key, session=s)


@pytest.mark.asyncio
async def test_run_query_with_read_time(
        creds: str, kind: str, project: str) -> None:
    test_value = f'read_time_test_{uuid.uuid4()}'

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)
        time_before_insert = datetime.datetime.utcnow()

        # Insert test data
        key = Key(project, [PathElement(kind)])
        await ds.insert(key, {'test_field': test_value}, session=s)

        # Test 1: insert and query for entity
        query = Query(
            kind=kind,
            query_filter=Filter(PropertyFilter(
                prop='test_field',
                operator=PropertyFilterOperator.EQUAL,
                value=Value(test_value)
            ))
        )

        result_current = await ds.runQuery(query, session=s)
        assert len(result_current.entity_results) == 1
        assert result_current.entity_results[0].entity.properties['test_field'] == test_value

        # Test 2: query w/ readTime
        current_time = datetime.datetime.utcnow()
        result_with_datetime = await ds.runQuery(query, read_time=current_time, session=s)
        assert len(result_with_datetime.entity_results) == 1
        # verify readTime is not empty and is between insertion and current
        # time
        assert result_with_datetime.read_time != ''
        read_time_dt = datetime.datetime.strptime(
            result_with_datetime.read_time[:-1], '%Y-%m-%dT%H:%M:%S.%f'
        )
        assert time_before_insert <= read_time_dt <= current_time

        # Test 3: query w/ readTime past insert time
        past_time = time_before_insert - datetime.timedelta(seconds=10)
        result_past = await ds.runQuery(query, read_time=past_time, session=s)
        assert len(result_past.entity_results) == 0

        # cleanup - delete the inserted data
        found_key = result_current.entity_results[0].entity.key
        await ds.delete(found_key, session=s)
