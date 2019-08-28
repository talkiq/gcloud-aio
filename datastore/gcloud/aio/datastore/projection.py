from typing import Any
from typing import Dict


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#Projection
class Projection:
    def __init__(self, prop: str) -> None:
        self.prop = prop

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Projection):
            return False

        return bool(self.prop == other.prop)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Projection':
        return cls(prop=data['property']['name'])

    def to_repr(self) -> Dict[str, Any]:
        return {
            'property': {'name': self.prop},
        }
