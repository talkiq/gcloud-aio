import io
import logging
import re
import threading
from dataclasses import dataclass
from email.message import Message
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import storage as aio_storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import ConnectionError as ConnectionFailure
    from requests import HTTPError as ResponseError
    from requests import Session
else:
    from aiohttp import ClientConnectionError as ConnectionFailure
    from aiohttp import ClientResponseError as ResponseError
    from aiohttp import ClientSession as Session


# pylint: disable=redefined-outer-name

# A request with this Content-Range is a status query, which GCS requires to
# have an empty body.
STATUS_QUERY = re.compile(r'^bytes \*/(\*|\d+)$')
RETRYABLE_STATUSES = [408, 429, 500, 502, 503, 504]
NON_RETRYABLE_STATUSES = [400, 401, 403, 404, 410, 412]
MAX_ATTEMPTS = 5
DATA = b'x' * 204800


@dataclass
class RecordedRequest:
    method: str
    headers: Message
    body: bytes


class FakeGcsServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statuses = []
        self.requests = []
        self.errors = []

    @property
    def url(self):
        ip, port = self.server_address
        return f'http://{ip}:{port}'

    @property
    def puts(self):
        return [r for r in self.requests if r.method == 'PUT']

    @property
    def posts(self):
        return [r for r in self.requests if r.method == 'POST']


class FakeGcsHandler(BaseHTTPRequestHandler):
    server: FakeGcsServer

    def log_message(self, *args):  # pylint: disable=arguments-differ
        pass

    def _record(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length)
        self.server.requests.append(
            RecordedRequest(self.command, self.headers, body),
        )
        return body

    def _respond(self, status, payload):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Location', self.server.url)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        self._record()
        self._respond(200, b'{}')

    def do_PUT(self):
        body = self._record()
        attempt = len(self.server.puts)

        content_range = self.headers.get('Content-Range', '')
        if STATUS_QUERY.match(content_range) and body:
            self.server.errors.append(
                f'attempt {attempt}: status query with non-empty body',
            )
            self._respond(400, b'{"error": "non-empty status query"}')
            return

        if not self.server.statuses:
            self.server.errors.append(f'attempt {attempt}: unexpected PUT')
            self._respond(418, b'{"error": "unexpected request"}')
            return

        status = self.server.statuses.pop(0)
        self._respond(status, f'{{"attempt": {attempt}}}'.encode())


@pytest.fixture(scope='function')
def server():
    srv = FakeGcsServer(('localhost', 0), FakeGcsHandler)
    thread = threading.Thread(
        target=srv.serve_forever,
        kwargs={'poll_interval': 0.01},
    )
    thread.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        thread.join()
        srv.server_close()
    assert not srv.errors, srv.errors


@pytest.fixture(scope='function', autouse=True)
def retry_delays(monkeypatch):
    delays = []

    async def fake_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(aio_storage, 'sleep', fake_sleep)
    return delays


def status_of(error):
    if BUILD_GCLOUD_REST:
        return error.response.status_code
    return error.status


def retry_logs(caplog):
    return [
        r
        for r in caplog.records
        if r.name == aio_storage.log.name and 'Upload attempt' in r.message
    ]


async def upload(server, file_data=DATA, **kwargs):
    kwargs.setdefault('force_resumable_upload', True)
    kwargs.setdefault('content_type', 'text/plain')
    async with Session() as session:
        storage = aio_storage.Storage(session=session, api_root=server.url)
        return await storage.upload('bucket', 'object', file_data, **kwargs)


async def do_upload(server, stream, headers, **kwargs):
    async with Session() as session:
        storage = aio_storage.Storage(session=session, api_root=server.url)
        return await storage._do_upload(  # pylint: disable=protected-access
            server.url,
            stream,
            headers,
            session=session,
            **kwargs,
        )


# Retry policy


@pytest.mark.parametrize('status', RETRYABLE_STATUSES)
async def test_retries_retryable_status(server, retry_delays, status):
    server.statuses = [status, 200]

    response = await upload(server)

    assert response == {'attempt': 2}
    assert retry_delays == [1.0]


@pytest.mark.parametrize('status', NON_RETRYABLE_STATUSES)
async def test_does_not_retry_non_retryable_status(
    server,
    retry_delays,
    status,
):
    server.statuses = [status]

    with pytest.raises(ResponseError) as excinfo:
        await upload(server)

    assert status_of(excinfo.value) == status
    assert len(server.puts) == 1
    assert not retry_delays


async def test_gives_up_after_max_attempts(server, retry_delays):
    server.statuses = [500] * MAX_ATTEMPTS

    with pytest.raises(ResponseError) as excinfo:
        await upload(server)

    assert status_of(excinfo.value) == 500
    assert len(server.puts) == MAX_ATTEMPTS
    assert retry_delays == [1.0, 2.0, 4.0, 8.0]


async def test_does_not_retry_connection_errors(
    server,
    retry_delays,
    monkeypatch,
):
    async def failing_put(*args, **kwargs):
        raise ConnectionFailure('connection reset')

    monkeypatch.setattr(aio_storage.AioSession, 'put', failing_put)

    with pytest.raises(ConnectionFailure):
        await upload(server)

    assert not retry_delays


# Retried request contents


async def test_retry_never_sends_status_query(server):
    # Regression: retries used to set `Content-Range: bytes */*` while still
    # sending the body, which GCS rejects with a 400.
    server.statuses = [503, 200]
    headers = {}

    await upload(server, headers=headers)

    for request in server.puts:
        assert not STATUS_QUERY.match(request.headers.get('Content-Range', ''))
    assert 'Content-Range' not in headers


@pytest.mark.parametrize('content_range', [None, 'bytes 0-204799/204800'])
async def test_retry_resends_identical_request(server, content_range):
    server.statuses = [500, 200]
    headers = {'Content-Range': content_range} if content_range else {}

    await upload(server, headers=headers)

    first, second = server.puts
    assert first.body == second.body == DATA
    for header in (
        'Content-Length',
        'Content-Range',
        'Content-Type',
        'Authorization',
    ):
        assert first.headers.get(header) == second.headers.get(header)
    assert second.headers.get('Content-Range') == content_range


@pytest.mark.parametrize('stream_type', [io.BytesIO, io.StringIO])
async def test_retry_resends_body_for_stream_type(server, stream_type):
    server.statuses = [500, 200]
    data = DATA if stream_type is io.BytesIO else DATA.decode()

    await upload(server, stream_type(data))

    assert [r.body for r in server.puts] == [DATA, DATA]


async def test_retry_resends_from_original_stream_offset(server):
    server.statuses = [500, 200]
    stream = io.BytesIO(b'0123456789')
    stream.seek(4)
    headers = {'Content-Length': '6', 'Content-Range': 'bytes 4-9/10'}

    await do_upload(server, stream, headers)

    assert [r.body for r in server.puts] == [b'456789', b'456789']


# Stream lifecycle


@pytest.mark.parametrize(
    'statuses',
    [
        pytest.param([500, 200], id='retried-success'),
        pytest.param([500] * MAX_ATTEMPTS, id='exhausted-retries'),
        pytest.param([400], id='non-retryable'),
    ],
)
async def test_closes_stream(server, statuses):
    server.statuses = statuses
    stream = io.BytesIO(DATA)

    try:
        await upload(server, stream)
    except ResponseError:
        pass

    assert stream.closed


# Logging


async def test_logs_each_failed_attempt(server, caplog):
    server.statuses = [503, 400]

    with pytest.raises(ResponseError) as excinfo:
        await upload(server)

    assert status_of(excinfo.value) == 400
    records = retry_logs(caplog)
    assert [r.levelno for r in records] == [logging.WARNING] * 2
    assert [r.message for r in records] == [
        f'Upload attempt 1/{MAX_ATTEMPTS} failed with HTTP status 503',
        f'Upload attempt 2/{MAX_ATTEMPTS} failed with HTTP status 400',
    ]
