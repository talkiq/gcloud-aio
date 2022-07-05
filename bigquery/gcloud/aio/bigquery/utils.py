import datetime
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import List


log = logging.getLogger(__name__)


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
        f: Callable[[Any], Any] = {  # type: ignore[assignment]
            'BOOLEAN': lambda x: x == 'true',
            'BYTES': bytes,
            'FLOAT': float,
            'INTEGER': int,
            'NUMERIC': float,
            'RECORD': dict,
            'STRING': str,
            'TIMESTAMP': lambda x: datetime.datetime.fromtimestamp(float(x)),
        }[field['type']]
    except KeyError:
        # TODO: determine the proper methods for converting the following:
        # BIGNUMERIC
        # DATE
        # DATETIME
        # GEOGRAPHY
        # TIME
        log.error('Unsupported field type %s. Please open a bug report with '
                  'the following data: %s, %s', field['type'], field['mode'],
                  flatten(value))
        raise

    if field['mode'] == 'NULLABLE' and value is None:
        return value

    if field['mode'] == 'REPEATED':
        if field['type'] == 'RECORD':
            # TODO: The [0] and all this special-casing is suspicious. Is there
            # a case I'm missing with overly nested RECORDS, perhaps?
            # I suspect this entire block can get reduced down to a single case
            # and then inserted into the dict of Callables above.
            if (len(field['fields']) == 1
                    and field['fields'][0]['type'] == 'RECORD'):
                return [{f['name']: parse(f, xs)
                         for f in field['fields']}
                        for xs in flatten(value)]

            return [{f['name']: parse(f, x)
                     for f, x in zip(field['fields'], xs)}
                    for xs in flatten(value)]

        return [f(x) for x in flatten(value)]

    if field['type'] == 'RECORD':
        return {f['name']: parse(f, x)
                for f, x in zip(field['fields'], flatten(value))}

    return f(flatten(value))


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
    return [{k['name']: parse(k, v) for k, v in zip(fields, row)}
            for row in rows]
