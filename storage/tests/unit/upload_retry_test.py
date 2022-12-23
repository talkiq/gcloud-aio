import io
import json
import threading
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import storage as aio_storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


class StoppableHTTPServer(HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()


class FakeHttpServerHandler(BaseHTTPRequestHandler):
    def _read_and_write_data(self):
        content_len = int(self.headers.get('Content-Length'))
        data = self.rfile.read(content_len)
        payload = {'data': data.decode('utf-8')}
        json_payload = json.dumps(payload).encode('utf-8')
        self.wfile.write(json_payload)

    def _send_headers(self):
        url = 'http://{}:{}'.format(*self.server.server_address)

        self.send_header('Content-Type', 'text/json')
        self.send_header('Location', url)
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self._send_headers()
        self._read_and_write_data()

    def do_PUT(self):
        if 'Content-Range' not in self.headers:
            # Force a retry in storage._do_upload()
            # Without this retry, the test would pass
            self.send_response(500)
        else:
            self.send_response(200)
        self._send_headers()
        self._read_and_write_data()


@pytest.fixture(scope='function')
def fake_server():
    server = StoppableHTTPServer(('localhost', 0), FakeHttpServerHandler)
    server_url = 'http://{}:{}/'.format(*server.server_address)

    thread = threading.Thread(target=server.run)
    thread.start()
    yield server_url
    server.shutdown()
    thread.join()


@pytest.mark.asyncio
async def test_upload_retry(fake_server):  # pylint: disable=redefined-outer-name
    data_stream = io.BytesIO(b'test data')
    bucket_name = 'bucket'
    object_name = 'object'

    async with Session() as session:
        storage = aio_storage.Storage(session=session, api_root=fake_server)

        response = await storage.upload(
            bucket_name, object_name, content_type='text/plain',
            file_data=data_stream, force_resumable_upload=True,
        )

    assert response.get('data') == 'test data'
