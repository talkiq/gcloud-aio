import base64
import logging
import random

import aiohttp


log = logging.getLogger(__name__)


def backoff(base=2, factor=1.1, max_value=None):
    """Generator for exponential decay.

    The Google docs warn to back off from polling their API if there is no
    work available in a task queue. So we do.

    This method should be used as follows:
        my_backoff = backoff(...)
        ...
        if no_items_in_queue:
            time.sleep(next(my_backoff))
        else:
            my_backoff.send('reset')

    If its more convenient, you can re-initialize the generator rather than
    sending the `reset` event.

    Params:

        base: the mathematical base of the exponentiation operation
        factor: factor to multiply the exponentation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    def init():
        return 0

    n = init()

    while True:
        a = factor * base ** n

        if max_value is None or a < max_value:
            n += 1
            val = (yield a)
        else:
            val = (yield max_value - random.random() * max_value / 10)

        if val == 'reset':
            # generally, we discard the generator's output from calling
            #   backoff().send('reset')
            # so we init()-1 here to ensure the following call to
            #   next(backoff())
            # is correct
            n = init() - 1


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
