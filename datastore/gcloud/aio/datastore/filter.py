from typing import Any
from typing import Dict
from typing import List
from typing import Union

from .array import Array
from .constants import CompositeFilterOperator
from .constants import PropertyFilterOperator
from .value import Value


class BaseFilter:
    json_key: str

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'BaseFilter':
        raise NotImplementedError

    def to_repr(self) -> Dict[str, Any]:
        raise NotImplementedError


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#Filter
class Filter:
    def __init__(self, inner_filter: BaseFilter) -> None:
        self.inner_filter = inner_filter

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Filter):
            return False

        return self.inner_filter == other.inner_filter

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Filter':
        if 'compositeFilter' in data:
            return cls(CompositeFilter.from_repr(data['compositeFilter']))
        if 'propertyFilter' in data:
            return cls(PropertyFilter.from_repr(data['propertyFilter']))

        raise ValueError(f'invalid filter name: {data.keys()}')

    def to_repr(self) -> Dict[str, Any]:
        return {
            self.inner_filter.json_key: self.inner_filter.to_repr(),
        }


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#CompositeFilter
class CompositeFilter(BaseFilter):
    json_key = 'compositeFilter'

    def __init__(
        self, operator: CompositeFilterOperator,
        filters: List[Filter],
    ) -> None:
        self.operator = operator
        self.filters = filters

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CompositeFilter):
            return False

        return bool(
            self.operator == other.operator
            and self.filters == other.filters,
        )

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'CompositeFilter':
        operator = CompositeFilterOperator(data['op'])
        filters = [Filter.from_repr(f) for f in data['filters']]
        return cls(operator=operator, filters=filters)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'filters': [f.to_repr() for f in self.filters],
            'op': self.operator.value,
        }


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#PropertyFilter
class PropertyFilter(BaseFilter):
    json_key = 'propertyFilter'

    def __init__(
        self, prop: str, operator: PropertyFilterOperator,
        value: Union[Value, Array],
    ) -> None:
        self.prop = prop
        self.operator = operator
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PropertyFilter):
            return False

        return bool(
            self.prop == other.prop
            and self.operator == other.operator
            and self.value == other.value,
        )

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'PropertyFilter':
        prop = data['property']['name']
        operator = PropertyFilterOperator(data['op'])
        value = Value.from_repr(data['value'])
        return cls(prop=prop, operator=operator, value=value)

    def to_repr(self) -> Dict[str, Any]:
        rep: Dict[str, Any] = {
            'op': self.operator.value,
            'property': {'name': self.prop},
        }
        # TODO: consider refactoring to look more like Value.to_repr()
        if isinstance(self.value, Array):
            rep['value'] = {'arrayValue': self.value.to_repr()}
        elif (isinstance(self.value, Value)
              and isinstance(self.value.value, list)):
            # This allows for a bit of syntactic sugar such that folks can pass
            # in a list directly (ie. as a Value instead of as an Array, as the
            # Google APIs would return it).
            values = [Value(x).to_repr() for x in self.value.value]
            rep['value'] = {'arrayValue': {'values': values}}
        else:
            rep['value'] = self.value.to_repr()
        return rep
