from typing import Any
from typing import Dict
from typing import List

from gcloud.aio.datastore.constants import CompositeFilterOperator
from gcloud.aio.datastore.constants import PropertyFilterOperator
from gcloud.aio.datastore.value import Value


class _BaseFilter:
    json_key = ''

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> '_BaseFilter':
        raise NotImplementedError

    def to_repr(self) -> Dict[str, Any]:
        raise NotImplementedError


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#Filter
class Filter:
    def __init__(self, inner_filter: _BaseFilter):
        self.inner_filter = inner_filter

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Filter):
            return False
        return self.inner_filter == other.inner_filter

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Filter':
        (inner_filter_name, inner_filter_data), = data.items()
        if inner_filter_name == 'compositeFilter':
            inner_filter = CompositeFilter.from_repr(inner_filter_data)
        elif inner_filter_name == 'propertyFilter':
            inner_filter = PropertyFilter.from_repr(inner_filter_data)
        else:
            raise ValueError(f'Invalid filter name: {inner_filter_name}')
        return cls(inner_filter=inner_filter)

    def to_repr(self) -> Dict[str, Any]:
        return {
            self.inner_filter.__class__.json_key: self.inner_filter.to_repr()
        }


class CompositeFilter(_BaseFilter):
    json_key = 'compositeFilter'

    def __init__(
            self, operator: CompositeFilterOperator, filters: List[Filter]):
        self.operator = operator
        self.filters = filters

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CompositeFilter):
            return False
        return bool(
            self.operator == other.operator
            and self.filters == other.filters)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'CompositeFilter':
        operator = CompositeFilterOperator(data['op'])
        filters = [Filter.from_repr(f) for f in data['filters']]
        return cls(operator=operator, filters=filters)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'op': self.operator.value,
            'filters': [f.to_repr() for f in self.filters]
        }


class PropertyFilter(_BaseFilter):
    json_key = 'propertyFilter'

    def __init__(
            self, prop: str, operator: PropertyFilterOperator, value: Value):
        self.prop = prop
        self.operator = operator
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PropertyFilter):
            return False
        return bool(
            self.prop == other.prop
            and self.operator == other.operator
            and self.value == other.value)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'PropertyFilter':
        prop = data['property']['name']
        operator = PropertyFilterOperator(data['op'])
        value = Value.from_repr(data['value'])
        return cls(prop, operator, value)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'property': {'name': self.prop},
            'op': self.operator.value,
            'value': self.value.to_repr()
        }
