import base64
import sys
from typing import Union

def make_compatible_bytes_unicode(text: str):
    if sys.version_info[0] < 3:
        return unicode(text)  # pylint:disable=undefined-variable
    return bytes(text, 'utf-8')


def decode(payload: str) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
    return base64.b64decode(payload,
                            altchars=make_compatible_bytes_unicode('-_'))


def encode(payload: Union[bytes, str]) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    return base64.b64encode(payload,
                            altchars=make_compatible_bytes_unicode('-_'))
