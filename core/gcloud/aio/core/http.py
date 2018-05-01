from urllib.parse import quote_plus
from urllib.parse import urlencode

import aiohttp
import ujson
from asyncio_extras.contextmanager import async_contextmanager


@async_contextmanager
async def ensure_session(session):

    if session:
        yield session
    else:
        async with aiohttp.ClientSession() as session:
            yield session


async def post(url, payload=None, timeout=60, urlencoded=False,
               json_response=True, session=None, headers=None, params=None):
    # pylint: disable=too-many-arguments

    headers = headers or {}

    if urlencoded:

        if payload:
            payload = urlencode(payload, quote_via=quote_plus)

        headers['content-type'] = 'application/x-www-form-urlencoded'

    else:

        if payload:
            payload = ujson.dumps(payload)
            payload = payload.encode('utf-8')
            content_length = str(len(payload))
        else:
            content_length = '0'

        headers.update({
            'content-length': content_length,
            'content-type': 'application/json'
        })

    async with ensure_session(session) as s:  # pylint: disable=not-async-context-manager

        response = await s.post(
            url,
            data=payload,
            headers=headers,
            params=params,
            timeout=timeout
        )

        if json_response:
            content = await response.json()
        else:
            content = await response.text()

    return response.status, content
