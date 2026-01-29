from typing import Any

from .key import Key
from .value import Value


class Entity:
    key_kind = Key
    value_kind = Value

    def __init__(
            self, key: Key | None,
            properties: dict[str, dict[str, Any]] | None = None,
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
    def from_repr(cls, data: dict[str, Any]) -> 'Entity':
        # https://cloud.google.com/datastore/docs/reference/data/rest/v1/Entity
        # "for example, an entity in Value.entity_value may have no key"
        if data.get('key'):
            key: Key | None = cls.key_kind.from_repr(data['key'])
        else:
            key = None
        return cls(key, data.get('properties'))

    def to_repr(self) -> dict[str, Any]:
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
    def from_repr(cls, data: dict[str, Any]) -> 'EntityResult':
        return cls(
            cls.entity_kind.from_repr(data['entity']),
            data.get('version', ''),
            data.get('cursor', ''),
        )

    def to_repr(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            'entity': self.entity.to_repr(),
        }
        if self.version:
            data['version'] = self.version
        if self.cursor:
            data['cursor'] = self.cursor

        return data
