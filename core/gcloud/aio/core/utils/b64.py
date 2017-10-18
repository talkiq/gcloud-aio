import base64


def clean_b64decode(payload):

    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """

    return base64.b64decode(payload.replace('-', '+').replace('_', '/'))


def clean_b64encode(payload):

    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """

    if not isinstance(payload, bytes):
        payload = payload.encode('utf-8')

    return (
        base64.b64encode(payload)
        .replace(b'+', b'-')
        .replace(b'/', b'_')
        .decode('utf-8')
    )
