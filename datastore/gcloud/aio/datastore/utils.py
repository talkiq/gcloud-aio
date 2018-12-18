from typing import Any
from typing import Dict

from gcloud.aio.datastore.constants import FORMATTERS
from gcloud.aio.datastore.constants import TypeName
from gcloud.aio.datastore.constants import TYPES
from gcloud.aio.datastore.constants import UNFORMATTERS


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
