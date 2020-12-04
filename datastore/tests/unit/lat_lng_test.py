import pytest
from gcloud.aio.datastore import LatLng


class TestLatLng:
    @staticmethod
    def test_from_repr(lat_lng):
        original_latlng = lat_lng
        data = {
            'latitude': original_latlng.lat,
            'longitude': original_latlng.lon,
        }

        output_order = LatLng.from_repr(data)

        assert output_order == original_latlng

    @staticmethod
    def test_to_repr():
        lat = 49.2827
        lon = 123.1207
        latlng = LatLng(lat, lon)

        r = latlng.to_repr()

        assert r['latitude'] == lat
        assert r['longitude'] == lon

    @staticmethod
    def test_repr_returns_to_repr_as_string(lat_lng):
        assert repr(lat_lng) == str(lat_lng.to_repr())

    @staticmethod
    @pytest.fixture(scope='session')
    def lat_lng() -> LatLng:
        return LatLng(49.2827, 123.1207)
