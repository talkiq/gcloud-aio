import os
import uuid

import pytest
from gcloud.aio.datastore import Datastore


@pytest.mark.asyncio
async def test_item_lifecycle():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    kind_name = 'gcloud-aio-test'
    object_name = f'test_record_{uuid.uuid4()}'

    # TODO: need a `ds.get` to test these properly
    ds = Datastore(project, creds)

    props = {'is_this_bad_data': True}
    await ds.insert(kind_name, object_name, props)

    props = {'animal': 'aardvark', 'overwrote_bad_data': True}
    await ds.update(kind_name, object_name, props)

    props = {'meaning_of_life': 42}
    await ds.upsert(kind_name, object_name, props)
