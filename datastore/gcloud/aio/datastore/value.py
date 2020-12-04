import base64
from datetime import datetime
from typing import Any
from typing import Dict

from gcloud.aio.datastore.constants import TypeName
from gcloud.aio.datastore.constants import TYPES
from gcloud.aio.datastore.key import Key


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#value
class Value:  # pylint:disable=useless-object-inheritance
    key_kind = Key

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
        supported_types = cls._get_supported_types()
        for value_type, type_name in supported_types.items():
            json_key = type_name.value
            if json_key in data:
                if json_key == 'nullValue':
                    value: Any = None
                elif json_key == 'blobValue':
                    value = base64.b64decode(data[json_key])
                elif value_type == datetime:
                    date_string = data[json_key].rstrip('Z')[:26]
                    date_fmt = ('%Y-%m-%dT%H:%M:%S.%f'
                                if '.' in date_string else '%Y-%m-%dT%H:%M:%S')
                    value = datetime.strptime(date_string, date_fmt)
                elif hasattr(value_type, 'from_repr'):
                    value = value_type.from_repr(data[json_key])
                else:
                    value = value_type(data[json_key])
                break
        else:
            supported = [name.value for name in supported_types.values()]
            raise NotImplementedError(
                '{vals} does not contain a supported value type'
                ' (any of: {supported})'.format(vals=data.keys(),
                                                supported=supported))

        # Google may not populate that field. This can happen with both
        # indexed and non-indexed fields.
        exclude_from_indexes = bool(data.get('excludeFromIndexes', False))

        return cls(value=value, exclude_from_indexes=exclude_from_indexes)

    def to_repr(self) -> Dict[str, Any]:
        value_type = self._infer_type(self.value)
        if value_type in {TypeName.ARRAY, TypeName.ENTITY, TypeName.GEOPOINT,
                          TypeName.KEY}:
            value = self.value.to_repr()
        elif value_type == TypeName.TIMESTAMP:
            value = self.value.strftime('%Y-%m-%dT%H:%M:%S.%f000Z')
        elif value_type == TypeName.BLOB:
            value = base64.b64encode(self.value).decode('utf8')
        else:
            value = 'NULL_VALUE' if self.value is None else self.value
        return {
            'excludeFromIndexes': self.excludeFromIndexes,
            value_type.value: value,
        }

    def _infer_type(self, value: Any) -> TypeName:
        odd_strings = {'newstr', 'unicode'}
        kind = str if value.__class__.__name__ in odd_strings else type(value)
        supported_types = self._get_supported_types()

        try:
            return supported_types[kind]
        except KeyError:
            raise NotImplementedError(  # pylint: disable=raise-missing-from
                '{} is not a supported value type (any of: '
                '{})'.format(kind, supported_types))

    @classmethod
    def _get_supported_types(cls) -> Dict[Any, TypeName]:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from gcloud.aio.datastore import array
        from gcloud.aio.datastore import entity

        supported_types = TYPES
        supported_types.update({
            cls.key_kind: TypeName.KEY,
            array.Array: TypeName.ARRAY,
            entity.Entity: TypeName.ENTITY,
        })
        return supported_types
