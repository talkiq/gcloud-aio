import datetime
import decimal
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional


log = logging.getLogger(__name__)


try:
    utc = datetime.timezone.utc
except AttributeError:
    # build our own UTC for Python 2
    class UTC(datetime.tzinfo):
        def utcoffset(
            self,
            _dt: Optional[datetime.datetime],
        ) -> datetime.timedelta:
            return datetime.timedelta(0)

        def tzname(self, _dt: Optional[datetime.datetime]) -> str:
            return 'UTC'

        def dst(self, _dt: Optional[datetime.datetime]) -> datetime.timedelta:
            return datetime.timedelta(0)

    utc = UTC()  # type: ignore[assignment]


def flatten(x: Any) -> Any:
    """
    Flatten response objects into something we can actually work with.

    The API returns data of the form:

        {'f': [{'v': ...}]}

    to indicate groupings of fields and their potential for having multiple
    values. We want those to just be plain old objects.
    """
    if isinstance(x, dict):
        # TODO: what if a user has stored a dictionary in their table and that
        # dictionary is shaped the same way as Google's response format?
        if 'f' in x:
            return [flatten(y['v']) for y in x['f']]

        if 'v' in x:
            return flatten(x['v'])

    if isinstance(x, list):
        return [flatten(y) for y in x]

    return x


def parse(field: Dict[str, Any], value: Any) -> Any:
    """
    Parse a given field back to a Python object.

    This is often trivial: convert the value from a string to the type
    specified in the field's schema. There's a couple caveats we've identified
    so far, though:

    * NULLABLE fields should be handled specially, eg. so as not to
      accidentally convert them to the schema type.
    * REPEATED fields are nested a biot differently than expected, so we need
      to flatten *first*, then convert.

    `Field = Dict[str, Union[str, 'Field']]`, but wow is that difficult to
    represent in a backwards-enough compatible fashion.
    """
    try:
        convert: Callable[[Any], Any] = {  # type: ignore[assignment]
            'BIGNUMERIC': lambda x: decimal.Decimal(
                x, decimal.Context(prec=77),
            ),
            'BOOLEAN': lambda x: x == 'true',
            'BYTES': bytes,
            'FLOAT': float,
            'INTEGER': int,
            'NUMERIC': lambda x: decimal.Decimal(
                x, decimal.Context(prec=38),
            ),
            'RECORD': dict,
            'STRING': str,
            'TIMESTAMP': lambda x: datetime.datetime.fromtimestamp(
                float(x), tz=utc,
            ),
        }[field['type']]
    except KeyError:
        # TODO: determine the proper methods for converting the following:
        # DATE -> datetime?
        # DATETIME -> datetime?
        # GEOGRAPHY -> ??
        # TIME -> datetime?
        log.error(
            'Unsupported field type %s. Please open a bug report with '
            'the following data: %s, %s', field['type'], field['mode'],
            flatten(value),
        )
        raise

    if field['mode'] == 'NULLABLE' and value is None:
        return value

    if field['mode'] == 'REPEATED':
        if field['type'] == 'RECORD':
            return [{
                f['name']: parse(f, x)
                for f, x in zip(field['fields'], xs)
            }
                for xs in flatten(value)]

        return [convert(x) for x in flatten(value)]

    if field['type'] == 'RECORD':
        return {
            f['name']: parse(f, x)
            for f, x in zip(field['fields'], flatten(value))
        }

    return convert(flatten(value))


def query_response_to_dict(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a query response to a dictionary.

    API responses for job queries are packed into a difficult-to-use format.
    This method deserializes a response into a List of rows, with each row
    being a dictionary of field names to the row's value.

    This method also handles converting the values according to the schema
    defined in the response (eg. into builtin python types).
    """
    fields = response['schema'].get('fields', [])
    rows = [x['f'] for x in response.get('rows', [])]
    return [
        {k['name']: parse(k, v) for k, v in zip(fields, row)}
        for row in rows
    ]
