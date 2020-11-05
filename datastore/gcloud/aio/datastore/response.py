from typing import Any
from typing import Dict
from typing import List

from gcloud.aio.datastore.mutation import MutationResult


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit
class CommitResponse:
    mutation_result_kind = MutationResult

    def __init__(self, mutation_results: List[MutationResult],
                 index_updates: int) -> None:
        self.mutation_results = mutation_results
        self.index_updates = index_updates

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'CommitResponse':
        mutation_results = [cls.mutation_result_kind.from_repr(r)
                            for r in data['mutationResults']]
        index_updates: int = data['indexUpdates']
        return cls(mutation_results, index_updates)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'mutationResults': [r.to_repr() for r in self.mutation_results],
            'indexUpdates': self.index_updates,
        }
