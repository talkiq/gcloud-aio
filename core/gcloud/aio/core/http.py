import json
from urllib.parse import quote_plus
from urllib.parse import urlencode

import aiohttp
from asyncio_extras.contextmanager import async_contextmanager


class HttpError(Exception):
    pass


@async_contextmanager
async def ensure_session(session):

    if session:
        yield session
    else:
        async with aiohttp.ClientSession() as session:
            yield session


async def delete(url, headers=None, params=None, timeout=60, session=None):

    async with ensure_session(session) as s:  # pylint: disable=not-async-context-manager

        response = await s.delete(
            url,
            headers=headers,
            params=params,
            timeout=timeout
        )

        phrase = await response.text()

    return response.status, phrase


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
            payload = json.dumps(payload)
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


async def get(url, timeout=60, json_response=True, session=None, headers=None,
              params=None):
    # pylint: disable=too-many-arguments

    async with ensure_session(session) as s:  # pylint: disable=not-async-context-manager

        response = await s.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout
        )

        if json_response:
            content = await response.json()
        else:
            content = await response.text()

    return response.status, content


async def put(*args, **kwargs):  # pylint: disable=unused-argument

    raise Exception('Not implemented.')


async def patch(url, payload=None, timeout=60, session=None, headers=None,
                params=None):
    # pylint: disable=too-many-arguments

    headers = headers or {}

    if payload:
        payload = json.dumps(payload)
        payload = payload.encode('utf-8')
        content_length = str(len(payload))
    else:
        content_length = '0'

    headers.update({
        'content-length': content_length,
        'content-type': 'application/json'
    })

    async with ensure_session(session) as s:  # pylint: disable=not-async-context-manager

        response = await s.patch(
            url,
            data=payload,
            headers=headers,
            params=params,
            timeout=timeout
        )

        phrase = await response.text()

    return response.status, phrase
