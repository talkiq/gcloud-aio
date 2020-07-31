import logging
import threading
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from io import IOBase
from typing import Any
from typing import Dict

from .build_constants import BUILD_GCLOUD_REST


log = logging.getLogger(__name__)


class BaseSession:
    __metaclass__ = ABCMeta

    def __init__(self, session=None, conn_timeout: int = 10,
                 read_timeout: int = 10, verify_ssl: bool = True):
        self.conn_timeout = conn_timeout
        self.read_timeout = read_timeout
        self._session = session
        self._ssl = verify_ssl

    @abstractproperty
    def session(self):
        return self._session

    @abstractmethod
    def post(self, url: str, headers: Dict[str, str], data: str, timeout: int,
             params: Dict[str, str]):
        pass

    @abstractmethod
    def get(self, url: str, headers: Dict[str, str], timeout: int,
            params: Dict[str, str]):
        pass

    @abstractmethod
    def put(self, url: str, headers: Dict[str, str], data: IOBase,
            timeout: int):
        pass

    @abstractmethod
    def delete(self, url: str, headers: Dict[str, str], params: Dict[str, str],
               timeout: int):
        pass

    @abstractmethod
    def request(self, method: str, url: str, headers: Dict[str, str],
                auto_raise_for_status: bool = True, **kwargs: Any):
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
                conn_timeout=self.conn_timeout, read_timeout=self.read_timeout,
                connector=connector)
            return self._session

        async def post(self, url: str, headers: Dict[str, str],
                       data: str = None, timeout: int = 10,
                       params: Dict[str, str] = None
                       ) -> aiohttp.ClientResponse:
            resp = await self.session.post(url, data=data, headers=headers,
                                           timeout=timeout, params=params)
            await _raise_for_status(resp)
            return resp

        async def get(self, url: str, headers: Dict[str, str] = None,
                      timeout: int = 10, params: Dict[str, str] = None
                      ) -> aiohttp.ClientResponse:
            resp = await self.session.get(url, headers=headers, timeout=timeout,
                                          params=params)
            await _raise_for_status(resp)
            return resp

        async def put(self, url: str, headers: Dict[str, str], data: IOBase,
                      timeout: int = 10) -> aiohttp.ClientResponse:
            resp = await self.session.put(url, data=data, headers=headers,
                                          timeout=timeout)
            await _raise_for_status(resp)
            return resp

        async def delete(self, url: str, headers: Dict[str, str],
                         params: Dict[str, str], timeout: int = 10
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
                await self._session.close()


if BUILD_GCLOUD_REST:
    import requests

    class SyncSession(BaseSession):
        _google_api_lock = threading.RLock()

        @property
        def google_api_lock(self) -> threading.RLock:
            return SyncSession._google_api_lock  # pylint: disable=protected-access

        @property
        def session(self) -> requests.Session:
            self._session = self._session or requests.Session()
            self._session.verify = self._ssl
            return self._session

        def post(self, url: str, headers: Dict[str, str], data: str = None,
                 timeout: int = 10, params: Dict[str, str] = None
                 ) -> requests.Response:
            with self.google_api_lock:
                resp = self.session.post(url, data=data, headers=headers,
                                         timeout=timeout, params=params)
            resp.raise_for_status()
            return resp

        def get(self, url: str, headers: Dict[str, str] = None,
                timeout: int = 10, params: Dict[str, str] = None
                ) -> requests.Response:
            with self.google_api_lock:
                resp = self.session.get(url, headers=headers, timeout=timeout,
                                        params=params)
            resp.raise_for_status()
            return resp

        def put(self, url: str, headers: Dict[str, str], data: IOBase,
                timeout: int = 10) -> requests.Response:
            with self.google_api_lock:
                resp = self.session.put(url, data=data, headers=headers,
                                        timeout=timeout)
            resp.raise_for_status()
            return resp

        def delete(self, url: str, headers: Dict[str, str],
                   params: Dict[str, str], timeout: int = 10
                   ) -> requests.Response:
            with self.google_api_lock:
                resp = self.session.delete(url, params=params, headers=headers,
                                           timeout=timeout)
            resp.raise_for_status()
            return resp

        def request(self, method: str, url: str, headers: Dict[str, str],
                    auto_raise_for_status: bool = True, **kwargs: Any
                    ) -> requests.Response:
            with self.google_api_lock:
                resp = self.session.request(method, url, headers=headers,
                                            **kwargs)
            if auto_raise_for_status:
                resp.raise_for_status()
            return resp

        def close(self) -> None:
            if self._session:
                self._session.close()
