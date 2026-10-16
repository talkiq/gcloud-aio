import http.server
import json
import threading
from collections.abc import Iterator

import pytest


class BigqueryApiHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self) -> None:
        if self.path.endswith('/tables/missing'):
            self._send_json(404, {
                'error': {'code': 404, 'message': 'Not found: Table missing'},
            })
            return

        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        job_id = self.path.split('?')[0].rsplit('/jobs/', 1)[-1]
        self._send_json(200, {'jobReference': {'jobId': job_id}})

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers['Content-Length']))
        if self.path.endswith('/jobs'):
            self._send_json(200, {'jobReference': {'jobId': 'fake-job'}})
            return

        self._send_json(404, {'error': {'code': 404, 'message': 'Not found'}})

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope='module')
def api_root() -> Iterator[str]:
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), BigqueryApiHandler,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/bigquery/v2'
    server.shutdown()
    thread.join()
    server.server_close()
