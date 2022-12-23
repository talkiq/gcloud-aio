from typing import Any
from typing import Dict


# https://cloud.google.com/datastore/docs/reference/data/rest/Shared.Types/LatLng
class LatLng:
    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LatLng):
            return False

        return bool(
            self.lat == other.lat
            and self.lon == other.lon,
        )

    def __repr__(self) -> str:
        return str(self.to_repr())

    @classmethod
    def from_repr(cls, data: Dict[str, Any]) -> 'LatLng':
        lat = data['latitude']
        lon = data['longitude']
        return cls(lat=lat, lon=lon)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'latitude': self.lat,
            'longitude': self.lon,
        }
