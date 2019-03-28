from typing import Any
from typing import Dict


_JSON_KEYS = {
    type(None): 'nullValue',
    bool: 'booleanValue',
    int: 'integerValue',
    float: 'doubleValue',
    # TODO timestampValue
    # TODO keyValue
    str: 'stringValue',
    # TODO blobValue
    # TODO geoPointValue
    # TODO entityValue
    # TODO arrayValue
}

_VALUE_TYPES = {v: k for k, v in _JSON_KEYS.items()}


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#value
class Value:
    def __init__(self, value: Any, exclude_from_indexes: bool = False):
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
        for json_key, value_type in _VALUE_TYPES.items():
            if json_key in data:
                if json_key == 'nullValue':
                    value = None
                else:
                    value = value_type(data[json_key])
                break
        else:
            raise NotImplementedError(
                f"Dict '{str(data)}' does not contain a supported value key")
        exclude_from_indexes = bool(data['excludeFromIndexes'])

        return cls(value=value, exclude_from_indexes=exclude_from_indexes)

    def to_repr(self) -> Dict[str, Any]:
        value_type = type(self.value)
        if value_type not in _JSON_KEYS:
            raise NotImplementedError(
                f"Type '{value_type}' is not supported by the Value type")

        return {
            'excludeFromIndexes': self.excludeFromIndexes,
            _JSON_KEYS[value_type]: self.value or 'NULL_VALUE'
        }
