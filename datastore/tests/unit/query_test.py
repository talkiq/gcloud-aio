import pytest
from gcloud.aio.datastore import Direction
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import PropertyOrder
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import QueryResultBatch
from gcloud.aio.datastore import Value


class TestQuery:
    @staticmethod
    def test_from_repr(query):
        original_query = query
        data = {
            'kind': original_query.kind,
            'filter': original_query.query_filter.to_repr(),
        }

        output_query = Query.from_repr(data)

        assert output_query == original_query

    @staticmethod
    def test_from_repr_query_without_kind(query_filter):
        original_query = Query(kind='', query_filter=query_filter)
        data = {
            'kind': [],
            'filter': original_query.query_filter.to_repr(),
        }

        output_query = Query.from_repr(data)

        assert output_query == original_query

    @staticmethod
    def test_from_repr_query_with_several_orders():
        orders = [
            PropertyOrder('property1', direction=Direction.ASCENDING),
            PropertyOrder('property2', direction=Direction.DESCENDING),
        ]
        original_query = Query(order=orders)

        data = {
            'kind': [],
            'order': [
                {
                    'property': {
                        'name': orders[0].prop,
                    },
                    'direction': orders[0].direction,
                },
                {
                    'property': {
                        'name': orders[1].prop,
                    },
                    'direction': orders[1].direction,
                },
            ],
        }

        output_query = Query.from_repr(data)

        assert output_query == original_query

    @staticmethod
    def test_to_repr_simple_query():
        kind = 'foo'
        query = Query(kind)

        r = query.to_repr()

        assert len(r['kind']) == 1
        assert r['kind'][0]['name'] == kind

    @staticmethod
    def test_to_repr_query_without_kind():
        query = Query()

        r = query.to_repr()

        assert not r['kind']

    @staticmethod
    def test_to_repr_query_with_filter(query_filter):
        property_filter = query_filter
        query = Query('foo', property_filter)

        r = query.to_repr()

        assert r['filter'] == property_filter.to_repr()

    @staticmethod
    def test_to_repr_query_with_several_orders():
        orders = [
            PropertyOrder('property1', direction=Direction.ASCENDING),
            PropertyOrder('property2', direction=Direction.DESCENDING),
        ]
        query = Query(order=orders)

        r = query.to_repr()

        assert len(r['order']) == 2
        assert r['order'][0] == orders[0].to_repr()
        assert r['order'][1] == orders[1].to_repr()

    @staticmethod
    def test_repr_returns_to_repr_as_string(query):
        assert repr(query) == str(query.to_repr())

    @staticmethod
    def test_from_to_repr(query):
        new_query = Query.from_repr(query.to_repr())
        assert new_query == query

    @staticmethod
    @pytest.fixture(scope='session')
    def query(query_filter) -> Query:
        return Query('query_kind', query_filter)

    @staticmethod
    @pytest.fixture(scope='session')
    def query_filter() -> Filter:
        inner_filter = PropertyFilter(
            prop='property_name',
            operator=PropertyFilterOperator.EQUAL,
            value=Value(123),
        )
        return Filter(inner_filter)


class TestQueryResultBatch:
    @staticmethod
    def test_query_result_batch_with_read_time():
        data = {
            'endCursor': 'cursor123',
            'entityResultType': 'RESULT_TYPE_UNSPECIFIED',
            'entityResults': [],
            'moreResults': 'NO_MORE_RESULTS',
            'skippedResults': 0,
            'readTime': '2025-07-01T12:00:00Z'
        }

        batch = QueryResultBatch.from_repr(data)
        assert batch.read_time == '2025-07-01T12:00:00Z'

        result = batch.to_repr()
        assert result['readTime'] == '2025-07-01T12:00:00Z'

    @staticmethod
    def test_query_result_batch_without_read_time():
        data = {
            'endCursor': 'cursor123',
            'entityResultType': 'RESULT_TYPE_UNSPECIFIED',
            'entityResults': [],
            'moreResults': 'NO_MORE_RESULTS',
            'skippedResults': 0,
        }

        batch = QueryResultBatch.from_repr(data)
        assert batch.read_time is None

        result = batch.to_repr()
        assert 'readTime' not in result
