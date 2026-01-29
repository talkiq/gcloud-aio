from typing import Any


class DatastoreOperation:
    def __init__(
        self, name: str, done: bool,
        metadata: dict[str, Any] | None = None,
        error: dict[str, str] | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.done = done

        self.metadata = metadata
        self.error = error
        self.response = response

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: dict[str, Any]) -> 'DatastoreOperation':
        return cls(
            data['name'], data.get('done', False), data.get('metadata'),
            data.get('error'), data.get('response'),
        )

    def to_repr(self) -> dict[str, Any]:
        return {
            'done': self.done,
            'error': self.error,
            'metadata': self.metadata,
            'name': self.name,
            'response': self.response,
        }
