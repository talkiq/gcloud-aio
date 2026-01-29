"""Make sure all value types are serialized/deserialized correctly"""
import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import LatLng
from gcloud.aio.datastore import PathElement


@pytest.mark.asyncio
async def test_geo_point_value(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with Datastore(project=project, service_file=creds) as ds:

        allocatedKeys = await ds.allocateIds([key])
        await ds.reserveIds(allocatedKeys)

        props_insert = {'location': LatLng(49.2827, 123.1207)}
        await ds.insert(allocatedKeys[0], props_insert)
        actual = await ds.lookup([allocatedKeys[0]])
        assert actual['found'][0].entity.properties == props_insert
