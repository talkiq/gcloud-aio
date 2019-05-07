import gcloud.aio.datastore.datastore as datastore
from gcloud.aio.datastore.constants import TypeName
from gcloud.aio.datastore.utils import TYPES


def test_defining_custom_subclass_updates_list_of_types():
    class CustomKey:
        pass

    class CustomDatastore(datastore.Datastore):  # pylint: disable=unused-variable
        key_kind = CustomKey

    assert TYPES[CustomKey] == TypeName.KEY
