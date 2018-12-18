import uuid

import pytest
from gcloud.aio.datastore import Datastore


@pytest.mark.asyncio
async def test_item_lifecycle(creds, kind, project):
    object_name = f'test_record_{uuid.uuid4()}'

    # TODO: need a `ds.get` to test these properly
    ds = Datastore(project, creds)

    props = {'is_this_bad_data': True}
    await ds.insert(kind, object_name, props)

    props = {'animal': 'aardvark', 'overwrote_bad_data': True}
    await ds.update(kind, object_name, props)

    props = {'meaning_of_life': 42}
    await ds.upsert(kind, object_name, props)

    await ds.delete(kind, object_name)
