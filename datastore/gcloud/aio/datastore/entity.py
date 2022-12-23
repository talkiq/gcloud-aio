from typing import Any
from typing import Dict
from typing import Optional

from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.value import Value


class Entity:
    key_kind = Key
    value_kind = Value

    def __init__(
            self, key: Optional[Key],
            properties: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.key = key
        self.properties = {
            k: self.value_kind.from_repr(v).value
            for k, v in (properties or {}).items()
        }

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return False

        return bool(
            self.key == other.key
            and self.properties == other.properties,
        )

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Entity':
        # https://cloud.google.com/datastore/docs/reference/data/rest/v1/Entity
        # "for example, an entity in Value.entity_value may have no key"
        if 'key' in data:
            key: Optional[Key] = cls.key_kind.from_repr(data['key'])
        else:
            key = None
        return cls(key, data.get('properties'))

    def to_repr(self) -> Dict[str, Any]:
        return {
            'key': self.key.to_repr() if self.key else None,
            'properties': {
                k: self.value_kind(v).to_repr()
                for k, v in self.properties.items()
            },
        }


class EntityResult:
    entity_kind = Entity

    def __init__(
        self, entity: Entity, version: str = '',
        cursor: str = '',
    ) -> None:
        self.entity = entity
        self.version = version
        self.cursor = cursor

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EntityResult):
            return False

        return bool(
            self.entity == other.entity
            and self.version == other.version
            and self.cursor == self.cursor,
        )

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'EntityResult':
        return cls(
            cls.entity_kind.from_repr(data['entity']),
            data.get('version', ''),
            data.get('cursor', ''),
        )

    def to_repr(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'entity': self.entity.to_repr(),
        }
        if self.version:
            data['version'] = self.version
        if self.cursor:
            data['cursor'] = self.cursor

        return data
