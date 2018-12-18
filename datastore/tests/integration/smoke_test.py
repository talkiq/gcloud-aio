import uuid

import aiohttp
import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement


@pytest.mark.asyncio  # type: ignore
async def test_item_lifecycle(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project, creds, session=s)

        allocatedKeys = await ds.allocateIds([key], session=s)
        assert len(allocatedKeys) == 1
        key.path[-1].id = allocatedKeys[0].path[-1].id
        assert key == allocatedKeys[0]

        await ds.reserveIds(allocatedKeys, session=s)

        props: dict = {'is_this_bad_data': True}
        await ds.insert(allocatedKeys[0], props, session=s)
        # TODO: test with ds.get

        props = {'animal': 'aardvark', 'overwrote_bad_data': True}
        await ds.update(allocatedKeys[0], props, session=s)
        # TODO: test with ds.get

        props = {'meaning_of_life': 42}
        await ds.upsert(allocatedKeys[0], props, session=s)
        # TODO: test with ds.get

        await ds.delete(allocatedKeys[0], session=s)
        # TODO: test with ds.get


@pytest.mark.asyncio  # type: ignore
async def test_transaction(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind, name=f'test_record_{uuid.uuid4()}')])

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project, creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        mutations = [
            ds.make_mutation(Operation.INSERT, key,
                             properties={'animal': 'three-toed sloth'}),
            ds.make_mutation(Operation.UPDATE, key,
                             properties={'animal': 'aardvark'}),
        ]
        await ds.commit(transaction, mutations=mutations, session=s)
        # TODO: test with ds.get


@pytest.mark.asyncio  # type: ignore
async def test_rollback(creds: str, project: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        ds = Datastore(project, creds, session=s)

        transaction = await ds.beginTransaction(session=s)
        await ds.rollback(transaction, session=s)
