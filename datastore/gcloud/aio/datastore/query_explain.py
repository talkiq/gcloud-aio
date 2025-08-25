import enum
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


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


class IndexDefinition:
    """
    Represents an index that would be used in PlanSummary.

    Raw:
        [
          {
            "query_scope": "Collection group",
            "properties": "(done ASC, priority DESC, __name__ ASC)"
          }
        ]

    query_scope: "Collection group"
    properties: [("done", "ASC"), ("priority", "DESC"), ("__name__", "ASC")]
    """

    _PROPERTIES_PATTERN = re.compile(
        r'\s*([^\s,()]+)\s+(ASC|DESC)\s*',
        flags=re.IGNORECASE)

    def __init__(self, query_scope: str = '',
                 properties: Optional[List[Tuple[str, str]]] = None):
        self.query_scope = query_scope
        self.properties = properties or []

    def __repr__(self) -> str:
        return str(self.to_repr())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, IndexDefinition):
            return False
        return (self.query_scope == other.query_scope
                and self.properties == other.properties)

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'IndexDefinition':
        query_scope = ''
        properties = []

        if 'query_scope' in data:
            query_scope = data['query_scope']
        if 'properties' in data:
            properties_str = data['properties']
            properties = cls._PROPERTIES_PATTERN.findall(properties_str)

        return cls(query_scope=query_scope, properties=properties)

    def to_repr(self) -> Dict[str, Any]:
        value = ', '.join(f'{name} {order}' for name, order in self.properties)
        properties = f'({value})'
        return {'query_scope': self.query_scope, 'properties': properties}


class PlanSummary:
    """Container class for planSummary returned by query explain."""

    def __init__(self, indexes_used: Optional[List[IndexDefinition]] = None):
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
        index_definitions = []
        for index in indexes_used:
            index_definitions.append(IndexDefinition.from_repr(index))

        return cls(indexes_used=index_definitions)

    def to_repr(self) -> Dict[str, Any]:
        indexes_used = [index.to_repr() for index in self.indexes_used]
        return {'indexesUsed': indexes_used}


class ExecutionStats:
    """Container class for executionStats returned by analyze mode."""

    def __init__(self, results_returned: int = 0,
                 execution_duration: float = 0.0,
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

    @staticmethod
    def _parse_execution_duration(
            execution_duration: Optional[Union[str, float]]) -> float:
        """Convert execution_duration from str (e.g. "0.01785s") to float."""
        if isinstance(execution_duration, float):
            # avoid parsing if already a float
            return execution_duration
        if not isinstance(execution_duration,
                          str) or not execution_duration.endswith('s'):
            raise ValueError(f'executionDuration must be a str ending with '
                             f'"s", got: {execution_duration}.')
        return float(execution_duration.rstrip('s'))

    @staticmethod
    def _parse_debug_stats(debug_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Convert debug_stats values from str to int."""
        for key, val in debug_stats.items():
            if isinstance(val, str) and val.isdigit():
                debug_stats[key] = int(val)
            elif isinstance(val, dict):
                for nested_key, nested_val in val.items():
                    if isinstance(nested_val, str) and nested_val.isdigit():
                        val[nested_key] = int(nested_val)

        return debug_stats

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'ExecutionStats':
        return cls(
            results_returned=int(data.get('resultsReturned', 0)),
            execution_duration=cls._parse_execution_duration(
                data.get('executionDuration')),
            read_operations=int(data.get('readOperations', 0)),
            debug_stats=cls._parse_debug_stats(data.get('debugStats', {}))
        )

    def to_repr(self) -> Dict[str, Any]:
        return {
            'resultsReturned': self.results_returned,
            'executionDuration': self.execution_duration,
            'readOperations': self.read_operations,
            'debugStats': self.debug_stats
        }


class ExplainMetrics:
    """Container class for explainMetrics returned by query explain."""

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
