import json
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.datastore import Consistency
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

    # pylint: disable=protected-access
    @staticmethod
    async def test_build_read_options_priority():
        async with Datastore() as ds:
            dt_str = '2025-01-01T12:00:00Z'

            # transaction > readTime > consistency
            result = ds._build_read_options(
                Consistency.STRONG, None, 'txn123', dt_str
            )
            assert result == {'transaction': 'txn123'}

            # readTime > consistency
            result = ds._build_read_options(
                Consistency.STRONG, None, None, dt_str
            )
            assert result == {'readTime': '2025-01-01T12:00:00Z'}

            # fall back to consistency
            result = ds._build_read_options(
                Consistency.STRONG, None, None, None
            )
            assert result == {'readConsistency': 'STRONG'}

    @staticmethod
    async def test_extra_request_fields_merged_into_payload():
        class _WithSentinelField(Datastore):
            def _extra_request_fields(self) -> dict[str, Any]:
                return {'sentinel': 'injected'}

        posted_body: dict[str, Any] = {}

        async def _fake_post(self_session, url, headers, data=None, **kwargs):
            del self_session, url, headers, kwargs
            nonlocal posted_body
            if data:
                posted_body = json.loads(data)
            resp = MagicMock()
            resp.json = AsyncMock(
                return_value={'found': [], 'missing': [], 'deferred': []},
            )
            return resp

        key = Key('p', [PathElement('Kind')])
        with patch.object(AioSession, 'post', _fake_post):
            async with _WithSentinelField(project='p', api_root='http://dev/'
                                          ) as ds:
                await ds.lookup([key])

        assert posted_body.get('sentinel') == 'injected'

    @staticmethod
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')
