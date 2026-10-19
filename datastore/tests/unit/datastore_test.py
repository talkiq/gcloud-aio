import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from gcloud.aio.datastore import Consistency
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import ExplainOptions
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value
from gcloud.aio.datastore.transaction_options import ReadOnly
from gcloud.aio.datastore.transaction_options import TransactionOptions


class TestDatastore:
    @staticmethod
    @pytest.mark.parametrize(('options', 'read_options'), [
        ({}, {'readConsistency': 'EVENTUAL'}),
        ({'consistency': Consistency.STRONG}, {'readConsistency': 'STRONG'}),
        ({'transaction': 'txn123'}, {'transaction': 'txn123'}),
        ({'newTransaction': TransactionOptions(ReadOnly())},
         {'newTransaction': {'readOnly': {}}}),
        ({'read_time': '2025-01-01T12:00:00Z'},
         {'readTime': '2025-01-01T12:00:00Z'}),
    ])
    async def test_run_aggregation_query(options, read_options, mocker):
        response = {
            'batch': {'aggregationResults': [{
                'aggregateProperties': {'count': {'integerValue': '17'}},
            }]},
            'transaction': 'new-transaction',
        }
        session = MagicMock()
        session.close = AsyncMock()
        session.post = AsyncMock(return_value=AsyncMock())
        session.post.return_value.json.return_value = response
        mocker.patch('gcloud.aio.datastore.datastore.AioSession',
                     return_value=session)
        async with Datastore(
            project='test-project', namespace='test-namespace',
            api_root='http://localhost/v1',
        ) as ds:
            result = await ds.runAggregationQuery(
                Query(kind='Task', offset=2, limit=5),
                aggregations=[{'alias': 'count', 'count': {}}],
                timeout=3., **options,
            )

        assert result == response
        args, kwargs = session.post.call_args
        assert args == ('http://localhost/v1/projects/test-project:'
                        'runAggregationQuery',)
        assert kwargs['timeout'] == 3.
        assert json.loads(kwargs['data']) == {
            'partitionId': {
                'projectId': 'test-project', 'namespaceId': 'test-namespace',
            },
            'readOptions': read_options,
            'aggregationQuery': {
                'nestedQuery': {
                    'kind': [{'name': 'Task'}], 'offset': 2, 'limit': 5,
                },
                'aggregations': [{'alias': 'count', 'count': {}}],
            },
        }

    @staticmethod
    async def test_run_aggregation_query_request_options(mocker):
        session = MagicMock()
        session.close = AsyncMock()
        session.post = AsyncMock(return_value=AsyncMock())
        session.post.return_value.json.return_value = {'explainMetrics': {}}
        session_wrapper = mocker.patch(
            'gcloud.aio.datastore.datastore.AioSession', return_value=session,
        )
        async with Datastore(
            project='test-project', api_root='http://localhost/v1',
        ) as ds:
            result = await ds.runAggregationQuery(
                Query(kind='Task'),
                aggregations=[{'alias': 'count', 'count': {}}],
                explain_options=ExplainOptions.DEFAULT,
                additional_request_fields={'databaseId': 'test-database'},
                session=session,
            )

        body = json.loads(session.post.call_args.kwargs['data'])
        session_wrapper.assert_called_with(session)
        assert body['explainOptions'] == {'analyze': False}
        assert body['databaseId'] == 'test-database'
        assert result == {'explainMetrics': {}}

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
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')
