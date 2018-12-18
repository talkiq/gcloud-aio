from typing import Any
from typing import Dict
from typing import List


class PathElement:
    def __init__(self, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name

    @classmethod
    def from_repr(cls, data: Dict[str, str]) -> 'PathElement':
        return cls(data['kind'], data['name'])

    def to_repr(self) -> Dict[str, str]:
        return {'kind': self.kind, 'name': self.name}


class Key:
    def __init__(self, project: str, path: List[PathElement],
                 namespace: str = '') -> None:
        self.project = project
        self.namespace = namespace
        self.path = path

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Key':
        return cls(data['partitionId']['projectId'],
                   path=[PathElement.from_repr(p) for p in data['path']],
                   namespace=data['partitionId']['namespaceId'])

    def to_repr(self) -> Dict[str, Any]:
        return {
            'partitionId': {
                'projectId': self.project,
                'namespaceId': '',
            },
            'path': [p.to_repr() for p in self.path],
        }
