import base64
from typing import Union


def decode(payload: str) -> Union[bytes, str]:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _

    Taskqueue seems to optimistically decode bytes as utf-8 as delivered to
    AppEnigne. If successful it will return the data as a str, otherwise it
    will return as bytes.

    """
    payload_bytes = base64.b64decode(payload, altchars=b'-_')
    try:
        return payload_bytes.decode('utf-8')
    except UnicodeDecodeError:
        pass
    return payload_bytes


def encode(payload: Union[bytes, str]) -> bytes:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    return base64.b64encode(payload, altchars=b'-_')
