import base64
import sys
from typing import Union

from future.utils import native_str_to_bytes


def decode(payload: str) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """

    if isinstance(payload, str) and sys.version_info[0] < 3:
        # Base64 encode/decode does not accept `str` as input in python2
        payload = native_str_to_bytes(payload)

    return base64.b64decode(payload, altchars=b'-_')


def encode(payload: Union[bytes, str]) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    return base64.b64encode(payload, altchars=b'-_')
