import base64
import re
from typing import Union


INVALID_BASE64_CHARS = re.compile(r'[^A-Za-z0-9+/=]')


def decode(payload: str) -> Union[str, bytes]:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    variant = payload.replace('-', '+').replace('_', '/')
    return base64.b64decode(variant).decode()


def encode(payload: Union[str, bytes]) -> str:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    if not isinstance(payload, bytes):
      payload = payload.encode('utf-8')

    encoded = base64.b64encode(payload)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').decode('utf-8')


def valid_base64(data: str) -> bool:
    """
    Check that the data is made up of base64 valid chars.

    """
    return not bool(INVALID_BASE64_CHARS.search(data))
