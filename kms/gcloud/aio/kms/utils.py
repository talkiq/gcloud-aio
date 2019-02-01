# TODO: this file is copied from gcloud-aio-taskqueue
import base64
from typing import Union


def decode(payload: str) -> str:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    variant = payload.replace('-', '+').replace('_', '/')
    return base64.b64decode(variant).decode()


def encode(payload: Union[bytes, str]) -> str:
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    if not isinstance(payload, bytes):
        payload = payload.encode('utf-8')

    encoded = base64.b64encode(payload)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').decode('utf-8')
