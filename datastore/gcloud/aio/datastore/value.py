from datetime import datetime
from typing import Any
from typing import Dict

from gcloud.aio.datastore.constants import TYPES


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#value
class Value:
    def __init__(self, value: Any, exclude_from_indexes: bool = False) -> None:
        self.value = value
        self.excludeFromIndexes = exclude_from_indexes

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Value):
            return False

        return bool(
            self.excludeFromIndexes == other.excludeFromIndexes
            and self.value == other.value)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Value':
        for value_type, type_name in TYPES.items():
            json_key = type_name.value
            if json_key in data:
                if json_key == 'nullValue':
                    value = None
                elif value_type == datetime:  # no parsing needed
                    value = data[json_key]
                else:
                    value = value_type(data[json_key])
                break
        else:
            supported_types = [type_name.value for type_name in TYPES.values()]
            raise NotImplementedError(
                f'{data.keys()} does not contain a supported value type'
                f' (any of: {supported_types})')

        exclude_from_indexes = bool(data['excludeFromIndexes'])

        return cls(value=value, exclude_from_indexes=exclude_from_indexes)

    def to_repr(self) -> Dict[str, Any]:
        value_type = type(self.value)
        if value_type not in TYPES:
            raise NotImplementedError(f'type "{value_type}" is not supported '
                                      'by the Value type')

        return {
            'excludeFromIndexes': self.excludeFromIndexes,
            TYPES[value_type].value: self.value or 'NULL_VALUE',
        }
