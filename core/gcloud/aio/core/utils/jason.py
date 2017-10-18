import json


def json_read(file_name: str):

    with open(file_name, 'r') as f:
        data = f.read()

    return json.loads(data)


def extract_json_fields(content, spec):

    if 'error' in content:
        raise Exception('{}'.format(content))

    return {field: cast(content[field]) for field, cast in spec}
