from typing import Any
from typing import Dict
from typing import Optional


class DatastoreOperation:
    def __init__(self, name: str, done: bool,
                 metadata: Optional[Dict[str, Any]] = None,
                 error=None, response: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata
        self.done = done
        self.error = error
        self.response = response

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'DatastoreOperation':
        return cls(data.get('name'), data.get('done'), data.get('metadata'),
                   data.get('error'), data.get('response'))

    def to_repr(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'done': self.done,
            'metadata': self.metadata,
            'error': self.error,
            'response': self.response
        }
