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


NAMED_KEY = Key(
    'test-project', [PathElement('Kind', name='n')], database='eu-db',
)
DEFAULT_KEY = Key('test-project', [PathElement('Kind', name='n')])


def data_method_calls(key):
    """Every Datastore data method, as (name, positional args, response)."""
    return [
        ('lookup', ([key],), {}),
        ('runQuery', (Query(kind='Kind'),), {}),
        (
            'runAggregationQuery',
            (Query(kind='Kind'), [{'alias': 'count', 'count': {}}]),
            {},
        ),
        ('beginTransaction', (), {'transaction': 't'}),
        (
            'commit',
            (
                [Datastore.make_mutation(Operation.UPSERT, key, {'a': 1})],
                't',
            ),
            {},
        ),
        ('rollback', ('t',), {}),
        ('allocateIds', ([key],), {'keys': []}),
        # No database_id, so reserveIds has to use the client's database
        ('reserveIds', ([key],), {}),
    ]


DATA_METHOD_CALLS = data_method_calls(NAMED_KEY)
DEFAULT_DATA_METHOD_CALLS = data_method_calls(DEFAULT_KEY)


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
    @pytest.mark.parametrize(
        ('method', 'args', 'response'), DATA_METHOD_CALLS,
    )
    async def test_named_database_requests(
        method, args, response, mock_session,
    ):
        mock_session.post.return_value.json.return_value = response
        async with Datastore(
            project='test-project', api_root='http://localhost/v1',
            database='eu-db',
        ) as ds:
            await getattr(ds, method)(*args)

        kwargs = mock_session.post.call_args.kwargs
        body = json.loads(kwargs['data'])
        assert body['databaseId'] == 'eu-db'
        assert kwargs['headers']['x-goog-request-params'] == (
            'project_id=test-project&database_id=eu-db'
        )
        if method in ('runQuery', 'runAggregationQuery'):
            assert body['partitionId']['databaseId'] == 'eu-db'

    @staticmethod
    @pytest.mark.parametrize(
        ('method', 'args', 'response'), DEFAULT_DATA_METHOD_CALLS,
    )
    async def test_default_database_requests(
        method, args, response, mock_session,
    ):
        mock_session.post.return_value.json.return_value = response
        async with Datastore(
            project='test-project', api_root='http://localhost/v1',
        ) as ds:
            await getattr(ds, method)(*args)

        kwargs = mock_session.post.call_args.kwargs
        body = json.loads(kwargs['data']) if kwargs.get('data') else {}
        assert not body.get('databaseId')
        assert 'x-goog-request-params' not in kwargs['headers']
        if method in ('runQuery', 'runAggregationQuery'):
            assert 'databaseId' not in body['partitionId']

    @staticmethod
    @pytest.mark.parametrize('client_database', ['', 'eu-db'])
    async def test_reserve_ids_database_id_overrides_client(
        client_database, mock_session,
    ):
        key = Key(
            'test-project', [PathElement('Kind', name='n')], database='other',
        )
        async with Datastore(
            project='test-project', api_root='http://localhost/v1',
            database=client_database,
        ) as ds:
            await ds.reserveIds([key], database_id='other')

        kwargs = mock_session.post.call_args.kwargs
        assert json.loads(kwargs['data'])['databaseId'] == 'other'
        assert kwargs['headers']['x-goog-request-params'] == (
            'project_id=test-project&database_id=other'
        )

    @staticmethod
    async def test_export_named_database_raises(mock_session):
        async with Datastore(
            project='test-project', api_root='http://localhost/v1',
            database='eu-db',
        ) as ds:
            with pytest.raises(Exception, match='named database'):
                await ds.export('bucket')

        mock_session.post.assert_not_called()

    @staticmethod
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')

    @staticmethod
    @pytest.fixture(scope='function')
    def mock_session(mocker):
        session = MagicMock()
        session.close = AsyncMock()
        session.post = AsyncMock(return_value=AsyncMock())
        mocker.patch(
            'gcloud.aio.datastore.datastore.AioSession', return_value=session,
        )
        return session
