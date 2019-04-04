import pytest
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value


class TestQuery:

    @staticmethod
    def test_from_repr(query):
        original_query = query
        data = {
            'kind': original_query.kind,
            'filter': original_query.query_filter.to_repr()
        }

        output_query = Query.from_repr(data)

        assert output_query == original_query

    @staticmethod
    def test_from_repr_query_without_kind(query_filter):
        original_query = Query(kind='', query_filter=query_filter)
        data = {
            'kind': [],
            'filter': original_query.query_filter.to_repr()
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
    def test_repr_returns_to_repr_as_string(query):
        assert repr(query) == str(query.to_repr())

    @staticmethod
    @pytest.fixture()
    def query(query_filter) -> Query:
        return Query('query_kind', query_filter)

    @staticmethod
    @pytest.fixture()
    def query_filter() -> Filter:
        inner_filter = PropertyFilter(
            prop='property_name',
            operator=PropertyFilterOperator.EQUAL,
            value=Value(123))
        return Filter(inner_filter)
