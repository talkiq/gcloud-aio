import sys
from datetime import datetime

import pytest
from gcloud.aio.datastore import Key
from gcloud.aio.datastore import LatLng
from gcloud.aio.datastore import PathElement
from gcloud.aio.datastore import Value


class TestValue:
    @staticmethod
    @pytest.mark.parametrize('json_key,json_value', [
        ('booleanValue', True),
        ('doubleValue', 34.48),
        ('integerValue', 8483),
        ('stringValue', 'foobar'),
        ('booleanValue', False),
        ('doubleValue', 0.0),
        ('integerValue', 0),
        ('stringValue', ''),
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
    @pytest.mark.parametrize('v,expected', [
        ('1998-07-12T11:22:33.456789000Z',
         datetime(year=1998, month=7, day=12, hour=11,
                  minute=22, second=33, microsecond=456789)),
        ('1998-07-12T11:22:33.456789Z',
         datetime(year=1998, month=7, day=12, hour=11,
                  minute=22, second=33, microsecond=456789)),
        ('1998-07-12T11:22:33.456Z',
         datetime(year=1998, month=7, day=12, hour=11,
                  minute=22, second=33, microsecond=456000)),
        ('1998-07-12T11:22:33',
         datetime(year=1998, month=7, day=12, hour=11,
                  minute=22, second=33, microsecond=0)),
    ])
    def test_from_repr_with_datetime_value(v, expected):
        data = {
            'excludeFromIndexes': False,
            'timestampValue': v
        }

        value = Value.from_repr(data)
        assert value.value == expected

    @staticmethod
    @pytest.mark.skipif(sys.version_info[0] < 3,
                        reason='skipping because python2 has same '
                               'type for str and bytes')
    def test_from_repr_with_blob_value():
        data = {
            'excludedFromIndexed': False,
            'blobValue': 'Zm9vYmFy'
        }

        value = Value.from_repr(data)
        assert value.value == b'foobar'

    @staticmethod
    def test_from_repr_with_key_value(key):
        data = {
            'excludeFromIndexes': False,
            'keyValue': key.to_repr()
        }

        value = Value.from_repr(data)

        assert value.value == key

    @staticmethod
    def test_from_repr_with_geo_point_value(lat_lng):
        data = {
            'excludeFromIndexes': False,
            'geoPointValue': lat_lng.to_repr()
        }

        value = Value.from_repr(data)

        assert value.value == lat_lng

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
        (True, 'booleanValue'),
        (34.48, 'doubleValue'),
        (8483, 'integerValue'),
        ('foobar', 'stringValue'),
        (False, 'booleanValue'),
        (0.0, 'doubleValue'),
        (0, 'integerValue'),
        ('', 'stringValue'),
    ])
    def test_to_repr(v, expected_json_key):
        value = Value(v)

        r = value.to_repr()

        assert len(r) == 2  # Value + excludeFromIndexes
        assert r['excludeFromIndexes'] is False
        assert r[str(expected_json_key)] == v

    @staticmethod
    def test_to_repr_with_null_value():
        value = Value(None)

        r = value.to_repr()

        assert r['nullValue'] == 'NULL_VALUE'

    @staticmethod
    def test_to_repr_with_datetime_value():
        dt = datetime(year=2018, month=7, day=15, hour=11, minute=22,
                      second=33, microsecond=456789)
        value = Value(dt)

        r = value.to_repr()

        assert r['timestampValue'] == '2018-07-15T11:22:33.456789000Z'

    @pytest.mark.skipif(sys.version_info[0] < 3,
                        reason='skipping because python2 has same '
                               'type for str and bytes')
    @staticmethod
    def test_to_repr_with_blob_value():
        value = Value(b'foobar')

        r = value.to_repr()
        assert r['blobValue'] == 'Zm9vYmFy'

    @staticmethod
    def test_to_repr_with_key_value(key):
        value = Value(key)

        r = value.to_repr()

        assert r['keyValue'] == key.to_repr()

    @staticmethod
    def test_to_repr_with_custom_key_value():
        class CustomKey:
            @staticmethod
            def to_repr():
                return {'some': 'JSON'}

        class CustomValue(Value):
            key_kind = CustomKey

        key = CustomKey()
        value = CustomValue(key)

        r = value.to_repr()

        assert r['keyValue'] == key.to_repr()

    @staticmethod
    def test_to_repr_with_geo_point_value(lat_lng):
        value = Value(lat_lng)

        r = value.to_repr()

        assert r['geoPointValue'] == lat_lng.to_repr()

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

        with pytest.raises(Exception) as ex_info:
            value.to_repr()

        assert NonSupportedType.__name__ in ex_info.value.args[0]

    @staticmethod
    def test_repr_returns_to_repr_as_string(value):
        assert repr(value) == str(value.to_repr())

    @staticmethod
    @pytest.fixture(scope='session')
    def key() -> Key:
        path = PathElement(kind='my-kind', name='path-name')
        key = Key(project='my-project', path=[path], namespace='my-namespace')
        return key

    @staticmethod
    @pytest.fixture(scope='session')
    def lat_lng() -> LatLng:
        return LatLng(49.2827, 123.1207)

    @staticmethod
    @pytest.fixture(scope='session')
    def value() -> Value:
        return Value(value='foobar', exclude_from_indexes=False)
