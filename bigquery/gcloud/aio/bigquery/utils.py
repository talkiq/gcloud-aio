import datetime
from typing import Any
from typing import Callable
from typing import Dict
from typing import List


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
            print(x)
            nested = [flatten(y['v']) for y in x['f']]
            if len(nested) == 1:
                # Nested data is always in a list form, even if it's a single
                # value that cannot be REPEATED. Why? Who knows.
                return nested[0]
            return nested

        if 'v' in x:
            return flatten(x['v'])

    if isinstance(x, list):
        return [flatten(y) for y in x]

    return x


def parse(field: Dict[str, str], value: Any) -> Any:
    """
    Parse a given field back to a Python object.

    This is often trivial: convert the value from a string to the type
    specified in the field's schema. There's a couple caveats we've identified
    so far, though:

    * NULLABLE fields should be handled specially, eg. so as not to
      accidentally convert them to the schema type.
    * REPEATED fields are nested a biot differently than expected, so we need
      to flatten *first*, then convert.
    """
    f: Callable[[Any], Any] = {  # type: ignore[assignment]
        'BOOLEAN': lambda x: x == 'true',
        'FLOAT': float,
        'INTEGER': int,
        'RECORD': list,
        'STRING': str,
        'TIMESTAMP': lambda x: datetime.datetime.fromtimestamp(float(x)),
    }[field['type']]

    if field['mode'] == 'NULLABLE' and value is None:
        return value
    if field['mode'] == 'REPEATED':
        return [f(x) for x in flatten(value)]
    return f(flatten(value))


def from_query_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
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
