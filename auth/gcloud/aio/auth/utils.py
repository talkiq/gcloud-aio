import base64
from typing import Union

import aiohttp


def decode(payload: str) -> bytes:
    """
    Modified Base64 for URL variants exist, where the + and / characters of
    standard Base64 are respectively replaced by - and _.

    See https://en.wikipedia.org/wiki/Base64#URL_applications
    """
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


async def get_client_session(timeout: int = 10) -> aiohttp.ClientSession:
    # Note that a `ClientSession` must be created within a coroutine.
    major, minor, _ = aiohttp.__version__.split('.')
    if int(major) > 3 or int(major) == 3 and int(minor) >= 3:
        client_timeout = aiohttp.ClientTimeout(total=timeout, connect=timeout)
        return aiohttp.ClientSession(timeout=client_timeout)

    return aiohttp.ClientSession(conn_timeout=timeout, read_timeout=timeout)
