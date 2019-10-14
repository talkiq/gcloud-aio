"""Make sure all value types are serialized/deserialized correctly"""
import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint:disable=no-name-in-module
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import LatLng
from gcloud.aio.datastore import PathElement

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio  # type: ignore
async def test_geo_point_value(creds: str, kind: str, project: str) -> None:
    key = Key(project, [PathElement(kind)])

    async with Session(timeout=10) as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        allocatedKeys = await ds.allocateIds([key], session=s)
        await ds.reserveIds(allocatedKeys, session=s)

        props_insert = {'location': LatLng(49.2827, 123.1207)}
        await ds.insert(allocatedKeys[0], props_insert, session=s)
        actual = await ds.lookup([allocatedKeys[0]], session=s)
        assert actual['found'][0].entity.properties == props_insert
