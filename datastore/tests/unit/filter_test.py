from typing import Any
from typing import Dict
from typing import List

import pytest
from gcloud.aio.datastore import CompositeFilter
from gcloud.aio.datastore import CompositeFilterOperator
from gcloud.aio.datastore import Filter
from gcloud.aio.datastore import PropertyFilter
from gcloud.aio.datastore import PropertyFilterOperator
from gcloud.aio.datastore import Value


class TestFilter:
    @staticmethod
    def test_property_filter_from_repr(property_filters):
        original_filter = property_filters[0]
        data = {
            'property': {
                'name': original_filter.prop
            },
            'op': original_filter.operator,
            'value': original_filter.value.to_repr()
        }

        output_filter = PropertyFilter.from_repr(data)

        assert output_filter == original_filter

    def test_property_filter_to_repr(self, property_filters):
        property_filter = property_filters[0]
        query_filter = Filter(inner_filter=property_filter)

        r = query_filter.to_repr()

        self._assert_is_correct_prop_dict_for_property_filter(
            r['propertyFilter'], property_filter)

    @staticmethod
    def test_composite_filter_from_repr(property_filters):
        # pylint: disable=line-too-long
        original_filter = CompositeFilter(
            operator=CompositeFilterOperator.AND,
            filters=[
                Filter(property_filters[0]),
                Filter(property_filters[1]),
            ])
        data = {
            'op': original_filter.operator,
            'filters': [
                {
                    'propertyFilter': {
                        'property': {
                            'name': original_filter.filters[0].inner_filter.prop,
                        },
                        'op': original_filter.filters[0].inner_filter.operator,
                        'value': property_filters[0].value.to_repr(),
                    },
                },
                {
                    'propertyFilter': {
                        'property': {
                            'name': original_filter.filters[1].inner_filter.prop,
                        },
                        'op': original_filter.filters[1].inner_filter.operator,
                        'value': property_filters[1].value.to_repr(),
                    },
                },
            ],
        }

        output_filter = CompositeFilter.from_repr(data)

        assert output_filter == original_filter

    def test_composite_filter_to_repr(self, property_filters):
        composite_filter = CompositeFilter(
            operator=CompositeFilterOperator.AND,
            filters=[
                Filter(property_filters[0]),
                Filter(property_filters[1])
            ])
        query_filter = Filter(composite_filter)

        r = query_filter.to_repr()

        composite_filter_dict = r['compositeFilter']
        assert composite_filter_dict['op'] == 'AND'
        self._assert_is_correct_prop_dict_for_property_filter(
            composite_filter_dict['filters'][0]['propertyFilter'],
            property_filters[0])
        self._assert_is_correct_prop_dict_for_property_filter(
            composite_filter_dict['filters'][1]['propertyFilter'],
            property_filters[1])

    @staticmethod
    def test_filter_from_repr(composite_filter):
        original_filter = Filter(inner_filter=composite_filter)

        data = {
            'compositeFilter': original_filter.inner_filter.to_repr()
        }

        output_filter = Filter.from_repr(data)

        assert output_filter == original_filter

    @staticmethod
    def test_filter_from_repr_unexpected_filter_name():
        unexpected_filter_name = 'unexpectedFilterName'
        data = {
            unexpected_filter_name: 'DoesNotMatter'
        }

        with pytest.raises(ValueError) as ex_info:
            Filter.from_repr(data)

        assert unexpected_filter_name in ex_info.value.args[0]

    @staticmethod
    def test_filter_to_repr(composite_filter):
        test_filter = Filter(inner_filter=composite_filter)

        r = test_filter.to_repr()

        assert r['compositeFilter'] == test_filter.inner_filter.to_repr()

    @staticmethod
    def test_repr_returns_to_repr_as_string(query_filter):
        assert repr(query_filter) == str(query_filter.to_repr())

    @staticmethod
    @pytest.fixture(scope='session')
    def property_filters() -> List[PropertyFilter]:
        return [
            PropertyFilter(
                prop='prop1',
                operator=PropertyFilterOperator.LESS_THAN,
                value=Value('value1')
            ),
            PropertyFilter(
                prop='prop2',
                operator=PropertyFilterOperator.GREATER_THAN,
                value=Value(1234)
            )
        ]

    @staticmethod
    @pytest.fixture(scope='session')
    def composite_filter(property_filters) -> CompositeFilter:
        return CompositeFilter(
            operator=CompositeFilterOperator.AND,
            filters=[
                Filter(property_filters[0]),
                Filter(property_filters[1])
            ])

    @staticmethod
    @pytest.fixture(scope='session')
    def query_filter(composite_filter) -> Filter:
        return Filter(inner_filter=composite_filter)

    @staticmethod
    @pytest.fixture(scope='session')
    def value() -> Value:
        return Value('value')

    @staticmethod
    def _assert_is_correct_prop_dict_for_property_filter(
            prop_dict: Dict[str, Any], property_filter: PropertyFilter):
        assert prop_dict['property']['name'] == property_filter.prop
        assert prop_dict['op'] == property_filter.operator.value
        assert prop_dict['value'] == property_filter.value.to_repr()
