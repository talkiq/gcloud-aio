from typing import Any
from typing import Dict
from typing import Optional

from gcloud.aio.datastore.key import Key


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit#Mutation
class Mutation:
    # TODO: Use this Mutation class instead of datastore.make_mutation
    pass


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit#MutationResult
class MutationResult:
    key_kind = Key

    def __init__(self, key: Optional[Key], version: str,
                 conflict_detected: bool) -> None:
        self.key = key
        self.version = version
        self.conflict_detected = conflict_detected

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MutationResult):
            return False

        return bool(self.key == other.key and self.version == other.version)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'MutationResult':
        if 'key' in data:
            key: Optional[Key] = cls.key_kind.from_repr(data['key'])
        else:
            key = None
        version: str = data['version']
        conflict_detected: bool = data.get('conflictDetected', False)
        return cls(key, version, conflict_detected)

    def to_repr(self) -> Dict[str, Any]:
        data = {
            'version': self.version,
            'conflictDetected': self.conflict_detected
        }
        if self.key:
            data['key'] = self.key.to_repr()
        return data
