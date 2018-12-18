from typing import Any
from typing import Dict
from typing import List


class PathElement:
    # pylint: disable=too-few-public-methods
    def __init__(self, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name

    def to_repr(self) -> Dict[str, str]:
        return {'kind': self.kind, 'name': self.name}


class Key:
    # pylint: disable=too-few-public-methods
    def __init__(self, project: str, path: List[PathElement],
                 namespace: str = '') -> None:
        self.project = project
        self.namespace = namespace
        self.path = path

    def to_repr(self) -> Dict[str, Any]:
        return {
            'partitionId': {
                'projectId': self.project,
                'namespaceId': '',
            },
            'path': [p.to_repr() for p in self.path],
        }
