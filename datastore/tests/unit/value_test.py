import pytest
from gcloud.aio.datastore import Value


class TestValue:

    @pytest.mark.parametrize('json_key,json_value', [
        ('booleanValue', True),
        ('integerValue', 8483),
        ('doubleValue', 34.48),
        ('stringValue', 'foobar')
    ])
    def test_from_repr(self, json_key, json_value):
        data = {
            'excludeFromIndexes': False,
            json_key: json_value
        }

        value = Value.from_repr(data)

        assert value.excludeFromIndexes is False
        assert value.value == json_value

    def test_from_repr_with_null_value(self):
        data = {
            'excludeFromIndexes': False,
            'nullValue': 'NULL_VALUE'
        }

        value = Value.from_repr(data)

        assert value.excludeFromIndexes is False
        assert value.value is None

    def test_from_repr_could_not_find_supported_value_key(self):
        data = {
            'excludeFromIndexes': False,
        }

        with pytest.raises(NotImplementedError) as ex_info:
            Value.from_repr(data)

        assert str(data) in ex_info.value.args[0]

    @pytest.mark.parametrize('v,expected_json_key', [
        (True, 'booleanValue'),
        (8483, 'integerValue'),
        (34.48, 'doubleValue'),
        ('foobar', 'stringValue')
    ])
    def test_to_repr(self, v, expected_json_key):
        value = Value(v)

        r = value.to_repr()

        assert len(r) == 2  # Value + excludeFromIndexes
        assert r['excludeFromIndexes'] is False
        assert r[expected_json_key] == v

    def test_to_repr_with_null_value(self):
        value = Value(None)

        r = value.to_repr()

        assert r['nullValue'] == 'NULL_VALUE'

    def test_to_repr_exclude_from_indexes(self):
        value = Value(123, exclude_from_indexes=True)

        r = value.to_repr()

        assert r['excludeFromIndexes']

    def test_to_repr_non_supported_type(self):
        class NonSupportedType:
            pass
        value = Value(NonSupportedType())

        with pytest.raises(NotImplementedError) as ex_info:
            value.to_repr()

        assert NonSupportedType.__name__ in ex_info.value.args[0]

    def test_repr_returns_to_repr_as_string(self):
        value = self._create_value()

        assert repr(value) == str(value.to_repr())

    def _create_value(self):
        return Value(value='foobar', exclude_from_indexes=False)
