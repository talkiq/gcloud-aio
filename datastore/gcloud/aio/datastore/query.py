from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from gcloud.aio.datastore.constants import MoreResultsType
from gcloud.aio.datastore.constants import ResultType
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.filter import Filter
from gcloud.aio.datastore.projection import Projection
from gcloud.aio.datastore.property_order import PropertyOrder
from gcloud.aio.datastore.value import Value


class BaseQuery:
    json_key: str
    value_kind = Value

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'BaseQuery':
        raise NotImplementedError

    def to_repr(self) -> Dict[str, Any]:
        raise NotImplementedError


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#Query
class Query(BaseQuery):
    # pylint: disable=too-many-instance-attributes
    json_key = 'query'

    def __init__(
        self, kind: str = '', query_filter: Optional[Filter] = None,
        order: Optional[List[PropertyOrder]] = None,
        start_cursor: str = '', end_cursor: str = '',
        offset: Optional[int] = None, limit: Optional[int] = None,
        projection: Optional[List[Projection]] = None,
        distinct_on: Optional[List[str]] = None,
    ) -> None:
        self.kind = kind
        self.query_filter = query_filter
        self.orders = order or []
        self.start_cursor = start_cursor
        self.end_cursor = end_cursor
        self.offset = offset
        self.limit = limit
        self.projection = projection or []
        self.distinct_on = distinct_on or []

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Query):
            return False

        return bool(
            self.kind == other.kind
            and self.query_filter == other.query_filter,
        )

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'Query':
        kind = data['kind'] or ''  # Kind is required
        if not isinstance(kind, str):
            # If 'kind' is not a str, then the only other acceptable format
            # is the list of a single dict [{'name' : kind}] (see to_repr)
            kind = kind[0].get('name') or ''
        orders = [PropertyOrder.from_repr(o) for o in data.get('order', [])]
        start_cursor = data.get('startCursor') or ''
        end_cursor = data.get('endCursor') or ''
        offset = int(data['offset']) if 'offset' in data else None
        limit = int(data['limit']) if 'limit' in data else None
        projection = [
            Projection.from_repr(p)
            for p in data.get('projection', [])
        ]
        distinct_on = [d['name'] for d in data.get('distinct_on', [])]

        filter_ = data.get('filter')
        query_filter = Filter.from_repr(filter_) if filter_ else None

        return cls(
            kind=kind, query_filter=query_filter, order=orders,
            start_cursor=start_cursor, end_cursor=end_cursor,
            offset=offset, limit=limit,
            projection=projection, distinct_on=distinct_on,
        )

    def to_repr(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'kind': [{'name': self.kind}] if self.kind else [],
        }
        if self.query_filter:
            data['filter'] = self.query_filter.to_repr()
        if self.orders:
            data['order'] = [o.to_repr() for o in self.orders]
        if self.start_cursor:
            data['startCursor'] = self.start_cursor
        if self.end_cursor:
            data['endCursor'] = self.end_cursor
        if self.offset is not None:
            data['offset'] = self.offset
        if self.limit is not None:
            data['limit'] = self.limit
        if self.projection:
            data['projection'] = [p.to_repr() for p in self.projection]
        if self.distinct_on:
            data['distinctOn'] = [{'name': d} for d in self.distinct_on]
        return data


# https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery#gqlquery
class GQLQuery(BaseQuery):
    json_key = 'gqlQuery'

    def __init__(
        self, query_string: str, allow_literals: bool = True,
        named_bindings: Optional[Dict[str, Any]] = None,
        positional_bindings: Optional[List[Any]] = None,
    ) -> None:
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
            and self.positional_bindings == other.positional_bindings,
        )

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'GQLQuery':
        allow_literals = data['allowLiterals']
        query_string = data['queryString']
        named_bindings = {
            k: cls._param_from_repr(v)
            for k, v in data.get('namedBindings', {}).items()
        }
        positional_bindings = [
            cls._param_from_repr(v)
            for v in data.get('positionalBindings', [])
        ]
        return cls(
            query_string, allow_literals=allow_literals,
            named_bindings=named_bindings,
            positional_bindings=positional_bindings,
        )

    @classmethod
    def _param_from_repr(cls, param_repr: Dict[str, Any]) -> Any:
        if 'cursor' in param_repr:
            return GQLCursor(param_repr['cursor'])

        return cls.value_kind.from_repr(param_repr['value']).value

    def to_repr(self) -> Dict[str, Any]:
        return {
            'allowLiterals': self.allow_literals,
            'queryString': self.query_string,
            'namedBindings': {
                k: self._param_to_repr(v)
                for k, v in self.named_bindings.items()
            },
            'positionalBindings': [
                self._param_to_repr(v)
                for v in self.positional_bindings
            ],
        }

    def _param_to_repr(self, param: Any) -> Dict[str, Any]:
        if isinstance(param, GQLCursor):
            return {'cursor': param.value}

        return {'value': self.value_kind(param).to_repr()}


class GQLCursor:

    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, GQLCursor) and self.value == other.value


class QueryResultBatch:
    entity_result_kind = EntityResult

    def __init__(
        self, end_cursor: str,
        entity_result_type: ResultType = ResultType.UNSPECIFIED,
        entity_results: Optional[List[EntityResult]] = None,
        more_results: MoreResultsType = MoreResultsType.UNSPECIFIED,
        skipped_cursor: str = '', skipped_results: int = 0,
        snapshot_version: str = '',
    ) -> None:
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

        return bool(
            self.end_cursor == other.end_cursor
            and self.entity_result_type == other.entity_result_type
            and self.entity_results == other.entity_results
            and self.more_results == other.more_results
            and self.skipped_cursor == other.skipped_cursor
            and self.skipped_results == other.skipped_results
            and self.snapshot_version == other.snapshot_version,
        )

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'QueryResultBatch':
        end_cursor = data['endCursor']
        entity_result_type = ResultType(data['entityResultType'])
        entity_results = [
            cls.entity_result_kind.from_repr(er)
            for er in data.get('entityResults', [])
        ]
        more_results = MoreResultsType(data['moreResults'])
        skipped_cursor = data.get('skippedCursor', '')
        skipped_results = data.get('skippedResults', 0)
        snapshot_version = data.get('snapshotVersion', '')
        return cls(
            end_cursor, entity_result_type=entity_result_type,
            entity_results=entity_results, more_results=more_results,
            skipped_cursor=skipped_cursor,
            skipped_results=skipped_results,
            snapshot_version=snapshot_version,
        )

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
