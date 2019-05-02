import gcloud.aio.datastore.datastore as datastore
from gcloud.aio.datastore.constants import TypeName
from gcloud.aio.datastore.utils import TYPES


class TestDatastore:
    @staticmethod
    def test_defining_custom_subclass_updates_list_of_types():
        class CustomKey:
            pass

        class CustomEntity:
            pass

        class CustomEntityResult(datastore.EntityResult):
            entity_kind = CustomEntity

        class CustomDatastore(datastore.Datastore):  # pylint: disable=unused-variable
            key_kind = CustomKey
            entity_result_kind = CustomEntityResult

        assert TYPES[CustomKey] == TypeName.KEY
        assert TYPES[CustomEntity] == TypeName.ENTITY
