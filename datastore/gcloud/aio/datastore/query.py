from typing import Any
from typing import Dict
from typing import List

from gcloud.aio.datastore.constants import MoreResultsType
from gcloud.aio.datastore.constants import ResultType
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.filter import Filter
from gcloud.aio.datastore.utils import make_value
from gcloud.aio.datastore.utils import parse_value


class BaseQuery:
    json_key: str

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'BaseQuery':
        raise NotImplementedError

    def to_repr(self) -> Dict[str, Any]:
        raise NotImplementedError


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#Query
class Query(BaseQuery):
    json_key = 'query'

    def __init__(self, kind: str = '', query_filter: Filter = None) -> None:
        self.kind = kind
        self.query_filter = query_filter

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Query):
            return False

        return bool(
            self.kind == other.kind
            and self.query_filter == other.query_filter)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Query':
        kind = data['kind'] or ''
        query_filter = Filter.from_repr(data['filter'])
        return cls(kind=kind, query_filter=query_filter)

    def to_repr(self) -> Dict[str, Any]:
        data = {'kind': [{'name': self.kind}] if self.kind else []}
        if self.query_filter:
            data['filter'] = self.query_filter.to_repr()
        return data


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#gqlquery
class GQLQuery(BaseQuery):
    json_key = 'gqlQuery'

    def __init__(self, query_string: str, allow_literals: bool = True,
                 named_bindings: Dict[str, Any] = None,
                 positional_bindings: List[Any] = None) -> None:
        self.query_string = query_string
        self.allow_literals = allow_literals
        self.named_bindings = named_bindings or {}
        self.positional_bindings = positional_bindings or []

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GQLQuery):
            return False

        return bool(
            self.query_string == other.query_string
            and self.allow_literals == other.allow_literals
            and self.named_bindings == other.named_bindings
            and self.positional_bindings == other.positional_bindings)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'GQLQuery':
        allow_literals = data['allowLiterals']
        query_string = data['queryString']
        named_bindings = {k: parse_value(v['value'])
                          for k, v in data.get('namedBindings', {}).items()}
        positional_bindings = [parse_value(v['value'])
                               for v in data.get('positionalBindings', [])]
        return cls(query_string, allow_literals=allow_literals,
                   named_bindings=named_bindings,
                   positional_bindings=positional_bindings)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'allowLiterals': self.allow_literals,
            'queryString': self.query_string,
            'namedBindings': {k: {'value': make_value(v)}
                              for k, v in self.named_bindings.items()},
            'positionalBindings': [{'value': make_value(v)}
                                   for v in self.positional_bindings],
        }


class QueryResultBatch:
    entity_result_kind = EntityResult

    def __init__(self, end_cursor: str,
                 entity_result_type: ResultType = ResultType.UNSPECIFIED,
                 entity_results: List[EntityResult] = None,
                 more_results: MoreResultsType = MoreResultsType.UNSPECIFIED,
                 skipped_cursor: str = '', skipped_results: int = 0,
                 snapshot_version: str = '') -> None:
        self.end_cursor = end_cursor

        self.entity_result_type = entity_result_type
        self.entity_results = entity_results or []
        self.more_results = more_results
        self.skipped_cursor = skipped_cursor
        self.skipped_results = skipped_results
        self.snapshot_version = snapshot_version

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, QueryResultBatch):
            return False

        return bool(self.end_cursor == other.end_cursor
                    and self.entity_result_type == other.entity_result_type
                    and self.entity_results == other.entity_results
                    and self.more_results == other.more_results
                    and self.skipped_cursor == other.skipped_cursor
                    and self.skipped_results == other.skipped_results
                    and self.snapshot_version == other.snapshot_version)

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'QueryResultBatch':
        end_cursor = data['endCursor']
        entity_result_type = ResultType(data['entityResultType'])
        entity_results = [cls.entity_result_kind.from_repr(er)
                          for er in data.get('entityResults', [])]
        more_results = MoreResultsType(data['moreResults'])
        skipped_cursor = data.get('skippedCursor', '')
        skipped_results = data.get('skippedResults', 0)
        snapshot_version = data.get('snapshotVersion', '')
        return cls(end_cursor, entity_result_type=entity_result_type,
                   entity_results=entity_results, more_results=more_results,
                   skipped_cursor=skipped_cursor,
                   skipped_results=skipped_results,
                   snapshot_version=snapshot_version)

    def to_repr(self) -> Dict[str, Any]:
        data = {
            'endCursor': self.end_cursor,
            'entityResults': [er.to_repr() for er in self.entity_results],
            'entityResultType': self.entity_result_type.value,
            'moreResults': self.more_results.value,
            'skippedResults': self.skipped_results,
        }
        if self.skipped_cursor:
            data['skippedCursor'] = self.skipped_cursor
        if self.snapshot_version:
            data['snapshotVersion'] = self.snapshot_version

        return data
