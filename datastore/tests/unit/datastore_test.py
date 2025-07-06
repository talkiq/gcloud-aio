import pytest
from gcloud.aio.datastore import Consistency
from gcloud.aio.datastore import Datastore
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import Operation
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import Value


class TestDatastore:
    @staticmethod
    def test_make_mutation_from_value_object(key):
        value = Value(30, exclude_from_indexes=True)
        properties = {'value': value}

        results = Datastore.make_mutation(Operation.INSERT, key, properties)

        assert results['insert']['properties']['value'] == value.to_repr()

    @staticmethod
    def test_build_read_options_priority():
        ds = Datastore()

        # transaction take precedence over readTime/consistency
        result = ds._build_read_options(
            Consistency.STRONG, None, 'txn123', '2025-01-01T12:00:00.000Z'
        )
        assert result == {'transaction': 'txn123'}

        # readTime takes precedence over consistency
        result = ds._build_read_options(
            Consistency.STRONG, None, None, '2025-01-01T12:00:00.000Z'
        )
        assert result == {'readTime': '2025-01-01T12:00:00.000Z'}

        # we fall back to consistency if nothing else is provided
        result = ds._build_read_options(
            Consistency.EVENTUAL, None, None, None
        )
        assert result == {'readConsistency': 'EVENTUAL'}

    @staticmethod
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')
