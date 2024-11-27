from typing import Optional

import pytest
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import Value


class TestDatastore:
    @staticmethod
    def test_make_mutation_from_value_object(key):
        value = Value(30, exclude_from_indexes=True)
        properties = {'value': value}

        results = Datastore.make_mutation(Operation.INSERT, key, properties)

        assert results['insert']['properties']['value'] == value.to_repr()

    @staticmethod
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')

# =========
# client
# =========


class _MockToken:
    @staticmethod
    async def get() -> Optional[str]:
        return 'Unit-Test-Bearer-Token'


@pytest.mark.asyncio
async def test_client_api_is_dev():
    """
    Test that the api_is_dev constructor parameter controls whether the
    Authorization header is set on requests
    """
    api_root = 'https://foobar/v1'

    # With no API root specified, assume API not dev, so auth header should be
    # set
    async with Datastore(token=_MockToken()) as datastore:
        assert 'Authorization' in await datastore.headers()
    # If API root set and not otherwise specified, assume API is dev, so auth
    # header should not be set
    async with Datastore(api_root=api_root, token=_MockToken()) as datastore:
        assert 'Authorization' not in await datastore.headers()
    # If API specified to be dev, auth header should not be set
    async with Datastore(
            api_root=api_root, api_is_dev=True, token=_MockToken(),
    ) as datastore:
        assert 'Authorization' not in await datastore.headers()
    # If API specified to not be dev, auth header should be set
    async with Datastore(
            api_root=api_root, api_is_dev=False, token=_MockToken(),
    ) as datastore:
        assert 'Authorization' in await datastore.headers()
