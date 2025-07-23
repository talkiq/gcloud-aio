import enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .query import QueryResultBatch


class ExplainOptions(enum.Enum):
    """Options for query explain operations."""
    DEFAULT = False
    ANALYZE = True

    def to_repr(self) -> Dict[str, bool]:
        return {'analyze': self.value}

    @classmethod
    def from_repr(cls, data: Dict[str, bool]) -> 'ExplainOptions':
        analyze_value = data.get('analyze', False)
        return cls.ANALYZE if analyze_value else cls.DEFAULT


class PlanSummary:
    """Container class for planSummary returned by query explain."""

    def __init__(self, indexes_used: Optional[List[Dict[str, Any]]] = None):
        self.indexes_used = indexes_used or []

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanSummary):
            return False
        return self.indexes_used == other.indexes_used

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'PlanSummary':
        indexes_used = data.get('indexesUsed', [])
        # TODO: Consider level of abstraction for indexesUsed
        #  (keep as raw dict?)
        return cls(indexes_used=indexes_used)

    def to_repr(self) -> Dict[str, Any]:
        return {'indexesUsed': self.indexes_used}


class ExecutionStats:
    """Container class for executionStats returned by analyze mode."""

    def __init__(self, results_returned: int = 0,
                 execution_duration: str = '',
                 read_operations: int = 0,
                 debug_stats: Optional[Dict[str, Any]] = None):
        self.results_returned = results_returned
        self.execution_duration = execution_duration
        self.read_operations = read_operations
        self.debug_stats = debug_stats or {}

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionStats):
            return False
        return (self.results_returned == other.results_returned
                and self.execution_duration == other.execution_duration
                and self.read_operations == other.read_operations
                and self.debug_stats == other.debug_stats)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'ExecutionStats':
        # TODO: Consider whether to store values as str (raw API values)
        #  or store as int/floats. ExplainMetrics may be aggregated upstream
        return cls(
            results_returned=int(data.get('resultsReturned', 0)),
            execution_duration=data.get('executionDuration', ''),
            read_operations=int(data.get('readOperations', 0)),
            debug_stats=data.get('debugStats', {})
        )

    def to_repr(self) -> Dict[str, Any]:
        return {
            'resultsReturned': self.results_returned,
            'executionDuration': self.execution_duration,
            'readOperations': self.read_operations,
            'debugStats': self.debug_stats
        }


class ExplainMetrics:
    """Container class for explain metrics returned by query explain."""

    def __init__(self, plan_summary: Optional[PlanSummary] = None,
                 execution_stats: Optional[ExecutionStats] = None):
        self.plan_summary = plan_summary
        self.execution_stats = execution_stats

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExplainMetrics):
            return False
        return (self.plan_summary == other.plan_summary
                and self.execution_stats == other.execution_stats)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'ExplainMetrics':
        plan_summary = None
        execution_stats = None

        if 'planSummary' in data:
            plan_summary = PlanSummary.from_repr(data['planSummary'])

        if 'executionStats' in data:
            execution_stats = ExecutionStats.from_repr(data['executionStats'])

        return cls(plan_summary=plan_summary, execution_stats=execution_stats)

    def to_repr(self) -> Dict[str, Any]:
        explain_metrics = {}
        if self.plan_summary:
            explain_metrics['planSummary'] = self.plan_summary.to_repr()
        if self.execution_stats:
            explain_metrics['executionStats'] = self.execution_stats.to_repr()

        return explain_metrics


class QueryExplainResult:
    """
    Container class for result returned by a query explain operation.
    In the future, we can unify runQuery and runExplainQuery to return
    an instance of this class (rename to QueryResult).
    TODO: Consider how to handle returning entity results.
      Maybe implement this as an iterator, similar to google-cloud-datastore?
    """

    def __init__(self, result_batch: Optional[QueryResultBatch] = None,
                 explain_metrics: Optional[ExplainMetrics] = None):
        self.result_batch = result_batch
        self.explain_metrics = explain_metrics

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueryExplainResult):
            return False
        return (self.result_batch == other.result_batch
                and self.explain_metrics == other.explain_metrics)

    def get_result_batch(self) -> Optional[QueryResultBatch]:
        # Currently returns QueryResultBatch, which contains list of entities
        return self.result_batch

    def get_explain_metrics(self) -> Optional[ExplainMetrics]:
        return self.explain_metrics

    def get_plan_summary(self) -> Optional[PlanSummary]:
        # TODO: explain_metrics should always exist for QueryExplainResult
        if self.explain_metrics is not None:
            return self.explain_metrics.plan_summary
        return None

    def get_execution_stats(self) -> Optional[ExecutionStats]:
        if self.explain_metrics is not None:
            return self.explain_metrics.execution_stats
        return None

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'QueryExplainResult':
        result_batch = None
        explain_metrics = None

        if 'batch' in data:
            result_batch = QueryResultBatch.from_repr(data['batch'])
        if 'explainMetrics' in data:
            explain_metrics = ExplainMetrics.from_repr(data['explainMetrics'])

        return cls(result_batch=result_batch, explain_metrics=explain_metrics)

    def to_repr(self) -> Dict[str, Any]:
        result = {}
        if self.result_batch is not None:
            result['batch'] = self.result_batch.to_repr()
        if self.explain_metrics is not None:
            result['explainMetrics'] = self.explain_metrics.to_repr()
        return result
