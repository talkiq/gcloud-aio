import io

import pytest
from gcloud.aio.auth.build_constants import BUILD_GCLOUD_REST
from gcloud.aio.auth.session import AioSession

if BUILD_GCLOUD_REST:
    import requests
    import requests.adapters

    class FakeAdapter(requests.adapters.BaseAdapter):
        """Answer every request with a canned response, without a network."""

        def __init__(self, status: int, reason: str, body: bytes) -> None:
            super().__init__()
            self.status = status
            self.reason = reason
            self.body = body

        def send(self, request, **_):  # pylint: disable=arguments-differ
            resp = requests.Response()
            resp.status_code = self.status
            resp.reason = self.reason
            resp.headers['Content-Type'] = 'application/json; charset=UTF-8'
            resp.encoding = 'UTF-8'
            resp.raw = io.BytesIO(self.body)
            resp.url = request.url
            resp.request = request
            return resp

        def close(self) -> None:
            pass

    class Session(requests.Session):
        def __init__(self, *args, **kwargs) -> None:
            self._called = False
            super(requests.Session, self).__init__(*args, **kwargs)

        def close(self) -> None:
            self._called = True
            super(requests.Session, self).close()

        @property
        def closed(self) -> bool:
            return self._called

    requests.Session = Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
async def test_unmanaged_session():
    async with Session() as session:
        gcloud_session = AioSession(session=session)
        assert gcloud_session._shared_session  # pylint: disable=protected-access
        await gcloud_session.close()

        assert not session.closed


@pytest.mark.asyncio
async def test_managed_session():
    gcloud_session = AioSession()
    # create new session
    gcloud_session.session  # pylint: disable=pointless-statement
    if BUILD_GCLOUD_REST:
        gcloud_session._session = Session()  # pylint: disable=protected-access
    assert not gcloud_session._shared_session  # pylint: disable=protected-access
    await gcloud_session.close()

    assert gcloud_session._session.closed  # pylint: disable=protected-access


rest_only = pytest.mark.skipif(
    not BUILD_GCLOUD_REST, reason='SyncSession only exists in gcloud-rest-*',
)

URL = 'https://example.com/v1/resource'
ERROR_BODY = (
    b'{"error": {"code": 429, "message": "Quota exceeded", '
    b'"errors": [{"reason": "rateLimitExceeded"}]}}'
)
STATUS_LINE = f'429 Client Error: Too Many Requests for url: {URL}'


def _sync_session(status: int, reason: str, body: bytes) -> AioSession:
    session = requests.Session()
    adapter = FakeAdapter(  # pylint: disable=possibly-used-before-assignment
        status, reason, body,
    )
    session.mount('https://', adapter)
    return AioSession(session=session)


@rest_only
@pytest.mark.parametrize('verb,args,kwargs', [
    ('post', (URL,), {'headers': {}}),
    ('get', (URL,), {}),
    ('patch', (URL,), {'headers': {}}),
    ('put', (URL,), {'headers': {}, 'data': b''}),
    ('delete', (URL,), {'headers': {}}),
    ('head', (URL,), {}),
    ('request', ('GET', URL), {'headers': {}}),
])
@pytest.mark.asyncio
async def test_sync_error_includes_body(verb, args, kwargs):
    gcloud_session = _sync_session(429, 'Too Many Requests', ERROR_BODY)

    with pytest.raises(requests.HTTPError) as excinfo:
        await getattr(gcloud_session, verb)(*args, **kwargs)

    message = str(excinfo.value)
    assert message.startswith(STATUS_LINE)
    assert 'rateLimitExceeded' in message
    assert excinfo.value.response.status_code == 429
    assert excinfo.value.request.url == URL


@rest_only
@pytest.mark.asyncio
async def test_sync_error_body_is_truncated():
    gcloud_session = _sync_session(
        500, 'Internal Server Error', b'x' * 100_000,
    )

    with pytest.raises(requests.HTTPError) as excinfo:
        await gcloud_session.get(URL)

    message = str(excinfo.value)
    assert message.startswith('500 Server Error')
    assert 'xxxx' in message
    assert 'truncated' in message
    assert len(message) < 10_000


@rest_only
@pytest.mark.asyncio
async def test_sync_streamed_error_leaves_body_unread():
    gcloud_session = _sync_session(429, 'Too Many Requests', ERROR_BODY)

    with pytest.raises(requests.HTTPError) as excinfo:
        await gcloud_session.get(URL, stream=True)

    assert str(excinfo.value) == STATUS_LINE
    assert excinfo.value.response.raw.read() == ERROR_BODY


@rest_only
@pytest.mark.asyncio
async def test_sync_request_without_auto_raise_returns_error_response():
    gcloud_session = _sync_session(429, 'Too Many Requests', ERROR_BODY)

    resp = await gcloud_session.request(
        'GET', URL, headers={}, auto_raise_for_status=False,
    )

    assert resp.status_code == 429


@rest_only
@pytest.mark.asyncio
async def test_sync_success_is_returned_unchanged():
    gcloud_session = _sync_session(200, 'OK', b'{"ok": true}')

    resp = await gcloud_session.get(URL)

    assert resp.json() == {'ok': True}
