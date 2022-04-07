from typing import Any
from typing import Dict
from typing import List

import pytest
from gcloud.aio.datastore import GQLQuery
from gcloud.aio.datastore.query import GQLCursor


class TestGQLQuery:
    @staticmethod
    def test_from_repr(query):
        data = {
            'allowLiterals': query.allow_literals,
            'queryString': query.query_string,
            'namedBindings': {
                'string_param': {
                    'value': {
                        'stringValue': 'foo'
                    }
                },
                'cursor_param': {
                    'cursor': 'startCursor'
                }
            },
            'positionalBindings': [
                {'value': {'integerValue': '123'}},
                {'cursor': 'endCursor'}],
        }

        output_query = GQLQuery.from_repr(data)
        assert output_query == query

    @staticmethod
    def test_to_repr(query):
        data = {
            'allowLiterals': query.allow_literals,
            'queryString': query.query_string,
            'namedBindings': {
                'string_param': {
                    'value': {
                        'excludeFromIndexes': False,
                        'stringValue': 'foo'
                    }
                },
                'cursor_param': {
                    'cursor': 'startCursor'
                }
            },
            'positionalBindings': [
                {'value': {'excludeFromIndexes': False, 'integerValue': 123}},
                {'cursor': 'endCursor'}],
        }

        output_data = query.to_repr()

        assert output_data == data

    @staticmethod
    def test_to_repr_and_back(query):
        data = query.to_repr()

        assert GQLQuery.from_repr(data) == query

    @staticmethod
    def test_repr_returns_to_repr_as_string(query):
        assert repr(query) == str(query.to_repr())

    @staticmethod
    @pytest.fixture(scope='session')
    def query(named_bindings, positional_bindings) -> GQLQuery:
        return GQLQuery('query_string',
                        named_bindings=named_bindings,
                        positional_bindings=positional_bindings)

    @staticmethod
    @pytest.fixture(scope='session')
    def named_bindings() -> Dict[str, Any]:
        return {
            'string_param': 'foo',
            'cursor_param': GQLCursor('startCursor')
        }

    @staticmethod
    @pytest.fixture(scope='session')
    def positional_bindings() -> List[Any]:
        return [123, GQLCursor('endCursor')]
