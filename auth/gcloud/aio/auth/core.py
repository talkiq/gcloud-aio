from typing import Optional

from aiohttp import __version__
from aiohttp import ClientSession
from aiohttp import ClientTimeout


DEFAULT_TIMEOUT = 10


class BaseClient:
    def __init__(self, session: Optional[ClientSession] = None) -> None:
        self._session = session

    async def get_session(self,
                          s: Optional[ClientSession] = None) -> ClientSession:
        # N.B. a `ClientSession` must be created within a coroutine
        if not self._session:
            # TODO: deprecate support for aiohttp < 3.3.0
            major, minor, _ = __version__.split('.')
            if int(major) > 3 or int(major) == 3 and int(minor) >= 3:
                client_timeout = ClientTimeout(connect=DEFAULT_TIMEOUT,
                                               total=DEFAULT_TIMEOUT)
                self._session = ClientSession(timeout=client_timeout)
                return self._session

            self._session = ClientSession(conn_timeout=DEFAULT_TIMEOUT,
                                          read_timeout=DEFAULT_TIMEOUT)

        # use override session if provided
        return s or self._session
