import pytest
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import Query
from gcloud.aio.datastore import Value


class TestQuery:

    def test_create_query_without_kind_throws_not_implemented_error(self):
        with pytest.raises(NotImplementedError) as ex_info:
            Query(kind='')
        assert 'Kindless queries are not supported' in ex_info.value.args[0]

    def test_from_repr(self):
        original_query = self._create_query()
        data = {
            'kind': original_query.kind,
            'filter': original_query.query_filter.to_repr()
        }

        output_query = Query.from_repr(data)

        assert output_query == original_query

    def test_to_repr_simple_query(self):
        kind = 'foo'
        query = Query(kind)

        r = query.to_repr()

        assert len(r['kind']) == 1
        assert r['kind'][0]['name'] == kind

    def test_to_repr_query_with_filter(self):
        property_filter = self._create_filter()
        query = Query('foo', property_filter)

        r = query.to_repr()

        assert r['filter'] == property_filter.to_repr()

    def test_repr_returns_to_repr_as_string(self):
        query = self._create_query()

        assert repr(query) == str(query.to_repr())

    def _create_query(self):
        query_filter = self._create_filter()
        return Query('query_kind', query_filter)

    @staticmethod
    def _create_filter():
        inner_filter = PropertyFilter(
            prop='property_name',
            operator=PropertyFilterOperator.EQUAL,
            value=Value(123))
        return Filter(inner_filter)
