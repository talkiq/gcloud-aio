from datetime import datetime as dt
from typing import Any
from typing import Dict

from gcloud.aio.datastore.constants import FORMATTERS
from gcloud.aio.datastore.constants import TypeName
from gcloud.aio.datastore.constants import UNFORMATTERS


# TODO: add types for entityValue, geoPointValue and arrayValue
# NOTE: TypeName.KEY is added dynamically by the datastore
TYPES = {
    bool: TypeName.BOOLEAN,
    bytes: TypeName.BLOB,
    dt: TypeName.TIMESTAMP,
    float: TypeName.DOUBLE,
    int: TypeName.INTEGER,
    str: TypeName.STRING,
    type(None): TypeName.NULL,
}


def infer_type(value: Any) -> TypeName:
    kind = type(value)

    try:
        return TYPES[kind]
    except KeyError:
        raise Exception(f'unsupported value type {kind}')


def make_value(value: Any) -> Dict[str, Any]:
    type_name = infer_type(value)
    return {
        type_name.value: FORMATTERS.get(type_name, lambda v: v)(value),
    }


def parse_value(data: Dict[str, Any]) -> Any:
    type_name = list(data.keys())[0]
    value = list(data.values())[0]
    return UNFORMATTERS.get(TypeName(type_name), lambda v: v)(value)
