from datetime import datetime

import pytest
from gcloud.aio.datastore import Value


class TestValue:

    @staticmethod
    @pytest.mark.parametrize('json_key,json_value', [
        ('blobValue', bytes('foobar', 'utf-8')),
        ('booleanValue', True),
        ('doubleValue', 34.48),
        ('integerValue', 8483),
        ('stringValue', 'foobar'),
        ('timestampValue', datetime(year=1998, month=7, day=12)),
    ])
    def test_from_repr(json_key, json_value):
        data = {
            'excludeFromIndexes': False,
            json_key: json_value
        }

        value = Value.from_repr(data)

        assert value.excludeFromIndexes is False
        assert value.value == json_value

    @staticmethod
    def test_from_repr_with_null_value():
        data = {
            'excludeFromIndexes': False,
            'nullValue': 'NULL_VALUE'
        }

        value = Value.from_repr(data)

        assert value.excludeFromIndexes is False
        assert value.value is None

    @staticmethod
    def test_from_repr_could_not_find_supported_value_key():
        data = {
            'excludeFromIndexes': False,
        }

        with pytest.raises(NotImplementedError) as ex_info:
            Value.from_repr(data)

        assert 'excludeFromIndexes' in ex_info.value.args[0]

    @staticmethod
    @pytest.mark.parametrize('v,expected_json_key', [
        (bytes('foobar', 'utf-8'), 'blobValue'),
        (True, 'booleanValue'),
        (34.48, 'doubleValue'),
        (8483, 'integerValue'),
        ('foobar', 'stringValue'),
        (datetime(year=2018, month=7, day=15), 'timestampValue'),
    ])
    def test_to_repr(v, expected_json_key):
        value = Value(v)

        r = value.to_repr()

        assert len(r) == 2  # Value + excludeFromIndexes
        assert r['excludeFromIndexes'] is False
        assert r[expected_json_key] == v

    @staticmethod
    def test_to_repr_with_null_value():
        value = Value(None)

        r = value.to_repr()

        assert r['nullValue'] == 'NULL_VALUE'

    @staticmethod
    def test_to_repr_exclude_from_indexes():
        value = Value(123, exclude_from_indexes=True)

        r = value.to_repr()

        assert r['excludeFromIndexes']

    @staticmethod
    def test_to_repr_non_supported_type():
        class NonSupportedType:
            pass
        value = Value(NonSupportedType())

        with pytest.raises(NotImplementedError) as ex_info:
            value.to_repr()

        assert NonSupportedType.__name__ in ex_info.value.args[0]

    @staticmethod
    def test_repr_returns_to_repr_as_string(value):
        assert repr(value) == str(value.to_repr())

    @staticmethod
    @pytest.fixture()
    def value() -> Value:
        return Value(value='foobar', exclude_from_indexes=False)
