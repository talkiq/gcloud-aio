import gcloud.aio.datastore.datastore as datastore
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.value import Value


def test_defining_custom_subclass_updates_value_key_kind():
    class CustomKey:
        pass

    class CustomDatastore(datastore.Datastore):  # pylint: disable=unused-variable
        key_kind = CustomKey

    assert Value.key_kind == CustomKey

    Value.key_kind = Key  # Teardown
