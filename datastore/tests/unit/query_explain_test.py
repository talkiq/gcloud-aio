from gcloud.aio.datastore import ExecutionStats
from gcloud.aio.datastore import ExplainMetrics
from gcloud.aio.datastore import ExplainOptions
from gcloud.aio.datastore import IndexDefinition
from gcloud.aio.datastore import PlanSummary
from gcloud.aio.datastore import QueryResult
from gcloud.aio.datastore import QueryResultBatch


class TestExplainOptions:
    @staticmethod
    def test_enum_values():
        assert ExplainOptions.DEFAULT.value is False
        assert ExplainOptions.ANALYZE.value is True

        assert ExplainOptions.DEFAULT.to_repr() == {'analyze': False}
        assert ExplainOptions.ANALYZE.to_repr() == {'analyze': True}

        assert ExplainOptions.from_repr(
            {'analyze': False}) == ExplainOptions.DEFAULT
        assert ExplainOptions.from_repr(
            {'analyze': True}) == ExplainOptions.ANALYZE
        assert ExplainOptions.from_repr({}) == ExplainOptions.DEFAULT


class TestIndexDefinition:
    @staticmethod
    def test_from_repr_parsing():
        data = {
            'query_scope': 'Collection group',
            'properties': '(done ASC, priority DESC, __name__ ASC)'
        }

        index_def = IndexDefinition.from_repr(data)
        assert isinstance(index_def, IndexDefinition)
        assert index_def.query_scope == 'Collection group'
        assert index_def.properties == [
            ('done', 'ASC'), ('priority', 'DESC'), ('__name__', 'ASC')]

        assert index_def.to_repr() == data


# pylint: disable=line-too-long
class TestPlanSummary:
    @staticmethod
    def test_from_to_repr():
        data = {
            'indexesUsed': [
                {'query_scope': 'Collection',
                 'properties': '(prop1 ASC, __name__ ASC)'},
                {'query_scope': 'Collection group',
                 'properties': '(prop2 DESC, __name__ ASC)'}
            ]
        }

        plan_summary = PlanSummary.from_repr(data)
        assert isinstance(plan_summary, PlanSummary)

        assert len(plan_summary.indexes_used) == 2
        for index in plan_summary.indexes_used:
            assert isinstance(index, IndexDefinition)
        assert plan_summary.indexes_used[0].to_repr() == data['indexesUsed'][0]
        assert plan_summary.indexes_used[1].to_repr() == data['indexesUsed'][1]

        assert plan_summary.to_repr() == data
        assert repr(plan_summary) == str(plan_summary.to_repr())


# pylint: disable=line-too-long
class TestExecutionStats:
    @staticmethod
    def test_from_to_repr():
        data = {
            'resultsReturned': 45,
            'executionDuration': 0.021478,
            'readOperations': 50,
            'debugStats': {
                'billingDetails': {
                    'documentsScanned': 100,
                    'documentsReturned': 45,
                    'indexEntriesScanned': 150
                }
            }
        }

        execution_stats = ExecutionStats.from_repr(data)
        assert isinstance(execution_stats, ExecutionStats)

        assert execution_stats.results_returned == 45
        assert execution_stats.execution_duration == 0.021478
        assert execution_stats.read_operations == 50
        assert isinstance(execution_stats.debug_stats, dict)

        assert execution_stats.to_repr() == data
        assert repr(execution_stats) == str(execution_stats.to_repr())


class TestExplainMetrics:
    @staticmethod
    def test_from_to_repr_default_mode():
        data = {
            'planSummary': {
                'indexesUsed': [
                    {'query_scope': 'Collection',
                        'properties': '(chocolate DESC, __name__ ASC)'}
                ]
            }
        }

        explain_metrics = ExplainMetrics.from_repr(data)
        assert isinstance(explain_metrics, ExplainMetrics)

        assert isinstance(explain_metrics.plan_summary, PlanSummary)
        assert len(explain_metrics.plan_summary.indexes_used) == 1
        assert explain_metrics.execution_stats is None

        assert explain_metrics.to_repr() == data
        assert repr(explain_metrics) == str(explain_metrics.to_repr())

    @staticmethod
    def test_from_to_repr_analyze_mode():
        data = {
            'planSummary': {
                'indexesUsed': [
                    {'query_scope': 'Collection',
                     'properties': '(croissant ASC, __name__ ASC)'}
                ]
            },
            'executionStats': {
                'resultsReturned': 10,
                'executionDuration': 0.005,
                'readOperations': 10,
                'debugStats': {}
            }
        }

        explain_metrics = ExplainMetrics.from_repr(data)
        assert isinstance(explain_metrics, ExplainMetrics)

        assert isinstance(explain_metrics.plan_summary, PlanSummary)
        assert isinstance(explain_metrics.execution_stats, ExecutionStats)
        assert len(explain_metrics.plan_summary.indexes_used) == 1
        assert explain_metrics.execution_stats.results_returned == 10

        assert explain_metrics.to_repr() == data
        assert repr(explain_metrics) == str(explain_metrics.to_repr())


class TestQueryResult:
    @staticmethod
    def test_from_to_repr_default_mode():
        data = {
            'explainMetrics': {
                'planSummary': {
                    'indexesUsed': [
                        {
                            'query_scope': 'Collection',
                            'properties': '(strawberry DESC, __name__ ASC)'
                        }
                    ]
                }
            }
        }

        result = QueryResult.from_repr(data)
        assert isinstance(result, QueryResult)

        assert result.result_batch is None
        assert isinstance(result.explain_metrics, ExplainMetrics)
        assert isinstance(result.get_plan_summary(), PlanSummary)
        assert result.get_execution_stats() is None

        assert result.to_repr() == data
        assert repr(result) == str(result.to_repr())

    @staticmethod
    def test_from_to_repr_analyze_mode():
        data = {
            'batch': {
                'endCursor': 'abc123',
                'entityResults': [],
                'entityResultType': 'FULL',
                'moreResults': 'NO_MORE_RESULTS',
                'skippedResults': 5
            },
            'explainMetrics': {
                'planSummary': {
                    'indexesUsed': [
                        {'query_scope': 'Collection',
                         'properties': '(pineapple ASC, __name__ ASC)'}
                    ]
                },
                'executionStats': {
                    'resultsReturned': 0,
                    'executionDuration': 0.001,
                    'readOperations': 1,
                    'debugStats': {}
                }
            }
        }

        result = QueryResult.from_repr(data)
        assert isinstance(result, QueryResult)
        assert isinstance(result.result_batch, QueryResultBatch)
        assert isinstance(result.explain_metrics, ExplainMetrics)
        assert isinstance(result.get_plan_summary(), PlanSummary)
        assert isinstance(result.get_execution_stats(), ExecutionStats)

        assert result.to_repr() == data
        assert repr(result) == str(result.to_repr())
