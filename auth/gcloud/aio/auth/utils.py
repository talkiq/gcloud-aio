import base64


def decode(payload: str) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
    return base64.b64decode(payload, altchars=b'-_')


def encode(payload: bytes | str) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    return base64.b64encode(payload, altchars=b'-_')
