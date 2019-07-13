import base64
import logging

import aiohttp


log = logging.getLogger(__name__)


# TODO(nick): remove in favor of auth utils. Requires updating auth lib first.
def decode(payload):
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    variant = payload.replace('-', '+').replace('_', '/')
    return base64.b64decode(variant).decode()


def encode(payload):
    """
    https://en.wikipedia.org/wiki/Base64#URL_applications modified Base64
    for URL variants exist, where the + and / characters of standard
    Base64 are respectively replaced by - and _
    """
    if not isinstance(payload, bytes):
        payload = payload.encode('utf-8')

    encoded = base64.b64encode(payload)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').decode('utf-8')


async def raise_for_status(resp):
    if resp.status >= 400:
        try:
            log.error(await resp.json())
        except aiohttp.client_exceptions.ContentTypeError:
            log.error(await resp.text())

        raise aiohttp.client_exceptions.ClientResponseError(
            resp.request_info, resp.history, code=resp.status,
            headers=resp.headers, message=resp.reason)
