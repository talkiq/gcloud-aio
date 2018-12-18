import uuid

import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import PathElement


@pytest.mark.asyncio
async def test_item_lifecycle(creds, kind, project):
    object_name = f'test_record_{uuid.uuid4()}'

    # TODO: need a `ds.get` to test these properly
    ds = Datastore(project, creds)
    key = Key(project, [PathElement(kind, object_name)])

    allocatedKeys = await ds.allocateIds([key])
    assert len(allocatedKeys) == 1
    assert key == allocatedKeys[0]

    props = {'is_this_bad_data': True}
    await ds.insert(key, props)

    props = {'animal': 'aardvark', 'overwrote_bad_data': True}
    await ds.update(key, props)

    props = {'meaning_of_life': 42}
    await ds.upsert(key, props)

    await ds.delete(key)
