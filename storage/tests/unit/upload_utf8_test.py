import io
import json
import threading
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import storage as aio_storage

if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


class EchoHttpServerHandler(BaseHTTPRequestHandler):
    def _echo(self, upload_type):
        content_len = int(self.headers.get('Content-Length'))
        data = self.rfile.read(content_len)
        payload = json.dumps({
            'data': data.decode('utf-8'),
            'upload_type': upload_type,
        }).encode('utf-8')
        ip, port = self.server.server_address

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Location', f'http://{ip}:{port}/')
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        self._echo('simple')

    def do_PUT(self):
        self._echo('resumable')


@pytest.fixture(scope='function')
def fake_server():
    server = HTTPServer(('localhost', 0), EchoHttpServerHandler)
    ip, port = server.server_address
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={'poll_interval': 0.01},
    )
    thread.start()
    try:
        yield f'http://{ip}:{port}/'
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'upload_options',
    [
        pytest.param(
            {'force_resumable_upload': False},
            id='simple',
        ),
        pytest.param(
            {'force_resumable_upload': True},
            id='resumable',
        ),
        pytest.param(
            {'force_resumable_upload': None},
            id='automatic',
        ),
    ],
)
@pytest.mark.parametrize('as_stream', [False, True])
async def test_upload_utf8_content_length(
    fake_server,  # pylint: disable=redefined-outer-name
    upload_options,
    as_stream,
    monkeypatch,
):
    text = '中文abcdefgh'
    # Keep the test payload small while exercising byte-based type selection.
    monkeypatch.setattr(
        aio_storage,
        'MAX_CONTENT_LENGTH_SIMPLE_UPLOAD',
        len(text))
    file_data = io.StringIO(text) if as_stream else text

    async with Session() as session:
        storage = aio_storage.Storage(session=session, api_root=fake_server)

        response = await storage.upload(
            'bucket',
            'object',
            file_data=file_data,
            **upload_options,
        )

    assert response['data'] == text
    expected_type = (
        'simple'
        if upload_options['force_resumable_upload'] is False
        else 'resumable'
    )
    assert response['upload_type'] == expected_type


@pytest.mark.asyncio
@pytest.mark.parametrize('read_chars', [1, 10])
async def test_upload_utf8_stream_position(
    fake_server,  # pylint: disable=redefined-outer-name
    read_chars,
):
    text = '中文abcdefgh'
    file_data = io.StringIO(text)
    file_data.read(read_chars)

    async with Session() as session:
        storage = aio_storage.Storage(session=session, api_root=fake_server)

        response = await storage.upload(
            'bucket',
            'object',
            file_data=file_data,
            force_resumable_upload=False,
        )

    assert response['data'] == text[read_chars:]
