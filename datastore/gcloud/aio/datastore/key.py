from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class PathElement:
    def __init__(self, kind: str, *, id_: Optional[int] = None,
                 name: Optional[str] = None) -> None:
        self.kind = kind

        self.id = id_
        self.name = name
        if self.id and self.name:
            raise Exception('invalid PathElement contains both ID and name')

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PathElement):
            return False

        return bool(self.kind == other.kind and self.id == other.id
                    and self.name == other.name)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'PathElement':
        kind: str = data['kind']
        id_: Optional[int] = data.get('id')
        name: Optional[str] = data.get('name')
        return cls(kind, id_=id_, name=name)

    def to_repr(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {'kind': self.kind}
        if self.id:
            data['id'] = self.id
        elif self.name:
            data['name'] = self.name

        return data


class Key:
    path_element_kind = PathElement

    def __init__(self, project: str, path: List[PathElement],
                 namespace: str = '') -> None:
        self.project = project
        self.namespace = namespace
        self.path = path

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Key):
            return False

        return bool(self.project == other.project
                    and self.namespace == other.namespace
                    and self.path == other.path)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Key':
        return cls(data['partitionId']['projectId'],
                   path=[cls.path_element_kind.from_repr(p)
                         for p in data['path']],
                   namespace=data['partitionId'].get('namespaceId', ''))

    def to_repr(self) -> Dict[str, Any]:
        return {
            'partitionId': {
                'projectId': self.project,
                'namespaceId': self.namespace,
            },
            'path': [p.to_repr() for p in self.path],
        }
