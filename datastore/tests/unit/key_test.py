from gcloud.aio.datastore import Key
from gcloud.aio.datastore import PathElement


class TestKey:
    @staticmethod
    def test_to_repr_default_database():
        key = Key('p', [PathElement('K', name='n')])

        assert key.to_repr() == {
            'partitionId': {'projectId': 'p', 'namespaceId': ''},
            'path': [{'kind': 'K', 'name': 'n'}],
        }

    @staticmethod
    def test_named_database_round_trip():
        key = Key(
            'p', [PathElement('K', id_=123)], namespace='ns',
            database='eu-db',
        )

        data = key.to_repr()
        parsed = Key.from_repr(data)

        assert data['partitionId'] == {
            'projectId': 'p', 'namespaceId': 'ns', 'databaseId': 'eu-db',
        }
        assert parsed == key
        assert parsed.database == 'eu-db'

    @staticmethod
    def test_from_repr_subclass_without_database_argument():
        class KeyWithoutDatabaseArg(Key):
            def __init__(self, project, path, namespace=''):
                super().__init__(project, path, namespace=namespace)

        key = KeyWithoutDatabaseArg.from_repr({
            'partitionId': {'projectId': 'p', 'namespaceId': ''},
            'path': [{'kind': 'K', 'name': 'n'}],
        })

        assert key == Key('p', [PathElement('K', name='n')])

    @staticmethod
    def test_key_without_database_attribute():
        """eg. a Key unpickled from state saved without a database."""
        key = Key('p', [PathElement('K', name='n')])
        del key.__dict__['database']

        assert 'databaseId' not in key.to_repr()['partitionId']
        assert key == Key('p', [PathElement('K', name='n')])

    @staticmethod
    def test_keys_in_different_databases_are_not_equal():
        path = [PathElement('K', name='n')]

        assert Key('p', path, database='eu-db') != Key('p', path)
