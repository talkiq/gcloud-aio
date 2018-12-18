import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import PathElement


@pytest.mark.asyncio  # type: ignore
async def test_item_lifecycle(creds: str, kind: str, project: str) -> None:
    # TODO: need a `ds.get` to test these properly
    ds = Datastore(project, creds)
    key = Key(project, [PathElement(kind)])

    allocatedKeys = await ds.allocateIds([key])
    assert len(allocatedKeys) == 1
    key.path[-1].id = allocatedKeys[0].path[-1].id
    assert key == allocatedKeys[0]

    await ds.reserveIds(allocatedKeys)

    props: dict = {'is_this_bad_data': True}
    await ds.insert(allocatedKeys[0], props)

    props = {'animal': 'aardvark', 'overwrote_bad_data': True}
    await ds.update(allocatedKeys[0], props)

    props = {'meaning_of_life': 42}
    await ds.upsert(allocatedKeys[0], props)

    await ds.delete(allocatedKeys[0])
