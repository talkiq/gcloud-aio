from typing import Any
from typing import Dict

from gcloud.aio.datastore.constants import Direction


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#PropertyOrder
class PropertyOrder:
    def __init__(
        self, prop: str,
        direction: Direction = Direction.ASCENDING,
    ) -> None:
        self.prop = prop
        self.direction = direction

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PropertyOrder):
            return False

        return bool(
            self.prop == other.prop
            and self.direction == other.direction,
        )

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'PropertyOrder':
        prop = data['property']['name']
        direction = Direction(data['direction'])
        return cls(prop=prop, direction=direction)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'property': {'name': self.prop},
            'direction': self.direction.value,
        }
