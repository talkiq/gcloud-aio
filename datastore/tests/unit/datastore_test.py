import pytest
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
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        return Key(project='my-project', path=[path], namespace='my-namespace')
