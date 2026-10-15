import http.server
import json
import threading
from collections.abc import Iterator

import pytest


class TablesApiHandler(http.server.BaseHTTPRequestHandler):
    def do_DELETE(self) -> None:
        if self.path.endswith('/tables/missing'):
            body = json.dumps({
                'error': {'code': 404, 'message': 'Not found: Table missing'},
            }).encode()
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(204)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope='module')
def api_root() -> Iterator[str]:
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), TablesApiHandler,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/bigquery/v2'
    server.shutdown()
    thread.join()
    server.server_close()
