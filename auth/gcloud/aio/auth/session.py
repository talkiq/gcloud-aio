import logging
import threading
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from typing import Any
from typing import Dict
from typing import IO
from typing import Optional

from .build_constants import BUILD_GCLOUD_REST

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Response
    from requests import Session
else:
    from aiohttp import ClientResponse as Response  # type: ignore[no-redef]
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]


log = logging.getLogger(__name__)


class BaseSession:
    __metaclass__ = ABCMeta

    def __init__(self, session: Optional[Session] = None, timeout: int = 10,
                 verify_ssl: bool = True) -> None:
        self._session = session
        self._ssl = verify_ssl
        self._timeout = timeout

    @abstractproperty
    def session(self) -> Optional[Session]:
        return self._session

    @abstractmethod
    async def post(self, url: str, headers: Dict[str, str],
                   data: Optional[str], timeout: int,
                   params: Optional[Dict[str, str]]) -> Response:
        pass

    @abstractmethod
    async def get(self, url: str, headers: Optional[Dict[str, str]],
                  timeout: int, params: Optional[Dict[str, str]]) -> Response:
        pass

    @abstractmethod
    async def patch(self, url: str, headers: Dict[str, str],
                    data: Optional[str], timeout: int,
                    params: Optional[Dict[str, str]]) -> Response:
        pass

    @abstractmethod
    async def put(self, url: str, headers: Dict[str, str], data: IO[Any],
                  timeout: int) -> Response:
        pass

    @abstractmethod
    async def delete(self, url: str, headers: Dict[str, str],
                     params: Dict[str, str], timeout: int) -> Response:
        pass

    @abstractmethod
    async def request(self, method: str, url: str, headers: Dict[str, str],
                      auto_raise_for_status: bool = True,
                      **kwargs: Any) -> Response:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


if not BUILD_GCLOUD_REST:
    import aiohttp

    async def _raise_for_status(resp: aiohttp.ClientResponse) -> None:
        """Check resp for status and if error log additional info."""
        # Copied from aiohttp's raise_for_status() -- since it releases the
        # response payload, we need to grab the `resp.text` first to help users
        # debug.
        #
        # Useability/performance notes:
        # * grabbing the response can be slow for large files, only do it as
        #   needed
        # * we can't know in advance what encoding the files might have unless
        #   we're certain in advance that the result is an error payload from
        #   Google (otherwise, it could be a binary blob from GCS, for example)
        # * sometimes, errors are expected, so we should try to avoid polluting
        #   logs in that case
        #
        # https://github.com/aio-libs/aiohttp/blob/
        # 385b03ef21415d062886e1caab74eb5b93fdb887/aiohttp/
        # client_reqrep.py#L892-L902
        if resp.status >= 400:
            assert resp.reason is not None
            # Google's error messages are useful, pass 'em through
            body = await resp.text(errors='replace')
            resp.release()
            raise aiohttp.ClientResponseError(resp.request_info, resp.history,
                                              status=resp.status,
                                              message=f'{resp.reason}: {body}',
                                              headers=resp.headers)

    class AioSession(BaseSession):
        @property
        def session(self) -> aiohttp.ClientSession:
            connector = aiohttp.TCPConnector(ssl=self._ssl)
            self._session = self._session or aiohttp.ClientSession(
                connector=connector, timeout=self._timeout)
            return self._session

        async def post(self, url: str, headers: Dict[str, str],
                       data: Optional[str] = None, timeout: int = 10,
                       params: Optional[Dict[str, str]] = None
                       ) -> aiohttp.ClientResponse:
            resp = await self.session.post(url, data=data, headers=headers,
                                           timeout=timeout, params=params)
            await _raise_for_status(resp)
            return resp

        async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                      timeout: int = 10,
                      params: Optional[Dict[str, str]] = None
                      ) -> aiohttp.ClientResponse:
            resp = await self.session.get(url, headers=headers,
                                          timeout=timeout, params=params)
            await _raise_for_status(resp)
            return resp

        async def patch(self, url: str, headers: Dict[str, str],
                        data: Optional[str] = None, timeout: int = 10,
                        params: Optional[Dict[str, str]] = None
                        ) -> aiohttp.ClientResponse:
            resp = await self.session.patch(url, data=data, headers=headers,
                                            timeout=timeout, params=params)
            await _raise_for_status(resp)
            return resp

        async def put(self, url: str, headers: Dict[str, str], data: IO[Any],
                      timeout: int = 10) -> aiohttp.ClientResponse:
            resp = await self.session.put(url, data=data, headers=headers,
                                          timeout=timeout)
            await _raise_for_status(resp)
            return resp

        async def delete(self, url: str, headers: Dict[str, str],
                         params: Optional[Dict[str, str]] = None,
                         timeout: int = 10
                         ) -> aiohttp.ClientResponse:
            resp = await self.session.delete(url, headers=headers,
                                             params=params, timeout=timeout)
            await _raise_for_status(resp)
            return resp

        async def request(self, method: str, url: str, headers: Dict[str, str],
                          auto_raise_for_status: bool = True, **kwargs: Any
                          ) -> aiohttp.ClientResponse:
            resp = await self.session.request(method, url, headers=headers,
                                              **kwargs)
            if auto_raise_for_status:
                await _raise_for_status(resp)
            return resp

        async def close(self) -> None:
            if self._session:
                await self._session.close()  # type: ignore[func-returns-value]


if BUILD_GCLOUD_REST:
    class SyncSession(BaseSession):
        _google_api_lock = threading.RLock()

        @property
        def google_api_lock(self) -> threading.RLock:
            return SyncSession._google_api_lock  # pylint: disable=protected-access

        @property
        def session(self) -> Session:
            self._session = self._session or Session()
            self._session.verify = self._ssl
            return self._session

        # N.B.: none of these will be `async` in compiled form, but adding the
        # symbol ensures we match the base class's definition for static
        # analysis.
        async def post(self, url: str, headers: Dict[str, str],
                       data: Optional[str] = None, timeout: int = 10,
                       params: Optional[Dict[str, str]] = None) -> Response:
            with self.google_api_lock:
                resp = self.session.post(url, data=data, headers=headers,
                                         timeout=timeout, params=params)
            resp.raise_for_status()
            return resp

        async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                      timeout: int = 10,
                      params: Optional[Dict[str, str]] = None) -> Response:
            with self.google_api_lock:
                resp = self.session.get(url, headers=headers, timeout=timeout,
                                        params=params)
            resp.raise_for_status()
            return resp

        async def patch(self, url: str, headers: Dict[str, str],
                        data: Optional[str] = None, timeout: int = 10,
                        params: Optional[Dict[str, str]] = None) -> Response:
            with self.google_api_lock:
                resp = self.session.patch(url, data=data, headers=headers,
                                          timeout=timeout, params=params)
            resp.raise_for_status()
            return resp

        async def put(self, url: str, headers: Dict[str, str], data: IO[Any],
                      timeout: int = 10) -> Response:
            with self.google_api_lock:
                resp = self.session.put(url, data=data, headers=headers,
                                        timeout=timeout)
            resp.raise_for_status()
            return resp

        async def delete(self, url: str, headers: Dict[str, str],
                         params: Optional[Dict[str, str]] = None,
                         timeout: int = 10
                         ) -> Response:
            with self.google_api_lock:
                resp = self.session.delete(url, params=params, headers=headers,
                                           timeout=timeout)
            resp.raise_for_status()
            return resp

        async def request(self, method: str, url: str, headers: Dict[str, str],
                          auto_raise_for_status: bool = True, **kwargs: Any
                          ) -> Response:
            with self.google_api_lock:
                resp = self.session.request(method, url, headers=headers,
                                            **kwargs)
            if auto_raise_for_status:
                resp.raise_for_status()
            return resp

        async def close(self) -> None:
            if self._session:
                self._session.close()
