import asyncio
import enum
import io
import logging
import mimetypes
import os
from typing import Any
from typing import Optional
from typing import Tuple
from urllib.parse import quote

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.storage.bucket import Bucket
try:
    import ujson as json
except ModuleNotFoundError:
    import json  # type: ignore


API_ROOT = 'https://www.googleapis.com/storage/v1/b'
API_ROOT_UPLOAD = 'https://www.googleapis.com/upload/storage/v1/b'
SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write',
]

MAX_CONTENT_LENGTH_SIMPLE_UPLOAD = 5 * 1024 * 1024  # 5 MB


log = logging.getLogger(__name__)


class UploadType(enum.Enum):
    SIMPLE = 1
    RESUMABLE = 2


class Storage:
    def __init__(self, *, service_file: Optional[str] = None,
                 token: Optional[Token] = None,
                 session: Optional[aiohttp.ClientSession] = None) -> None:
        self.session = session
        self.token = token or Token(service_file=service_file,
                                    session=self.session, scopes=SCOPES)

    def get_bucket(self, bucket_name: str) -> Bucket:
        return Bucket(self, bucket_name)

    async def delete(self, bucket: str, object_name: str, *,
                     params: dict = None, timeout: int = 10,
                     session: aiohttp.ClientSession = None) -> str:
        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.delete(url, headers=headers, params=params or {},
                                    timeout=timeout)
        resp.raise_for_status()
        data: str = await resp.text()
        return data

    async def download(self, bucket: str, object_name: str, *,
                       timeout: int = 10,
                       session: aiohttp.ClientSession = None) -> bytes:
        return await self._download(bucket, object_name, timeout=timeout,
                                    params={'alt': 'media'}, session=session)

    async def download_metadata(self, bucket: str, object_name: str, *,
                                timeout: int = 10,
                                session: aiohttp.ClientSession = None) -> dict:
        data = await self._download(bucket, object_name, timeout=timeout,
                                    session=session)
        metadata: dict = json.loads(data.decode())
        return metadata

    async def list_objects(self, bucket: str, *, params: dict = None,
                           session: aiohttp.ClientSession = None,
                           timeout: int = 10) -> dict:
        token = await self.token.get()
        url = f'{API_ROOT}/{bucket}/o'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.get(url, headers=headers, params=params or {},
                                 timeout=timeout)
        resp.raise_for_status()
        data: dict = await resp.json()
        return data

    async def upload(self, bucket: str, object_name: str, file_data: Any,
                     *, content_type: str = None, headers: dict = None,
                     session: aiohttp.ClientSession = None, timeout: int = 30,
                     force_resumable_upload: bool = None) -> dict:
        token = await self.token.get()
        url = f'{API_ROOT_UPLOAD}/{bucket}/o'

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session

        stream = self._preprocess_data(file_data)
        content_length = self._get_stream_len(stream)

        # mime detection method same as in aiohttp 3.4.4
        content_type = content_type or mimetypes.guess_type(object_name)[0]

        headers = headers or {}
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Length': str(content_length),
            'Content-Type': content_type or '',
        })

        upload_type = self._decide_upload_type(force_resumable_upload,
                                               content_length)
        log.debug('using %r gcloud storage upload method', upload_type)

        if upload_type == UploadType.SIMPLE:
            return await self._upload_simple(url, object_name, stream, headers,
                                             session=session, timeout=timeout)

        if upload_type == UploadType.RESUMABLE:
            return await self._upload_resumable(url, object_name, stream,
                                                headers, session=session,
                                                timeout=timeout)

        raise TypeError(f'upload type {upload_type} not supported')

    @staticmethod
    def _get_stream_len(stream: io.IOBase) -> int:
        current = stream.tell()
        try:
            return stream.seek(0, os.SEEK_END)
        finally:
            stream.seek(current)

    @staticmethod
    def _preprocess_data(data: Any) -> io.IOBase:
        if data is None:
            return io.StringIO('')

        if isinstance(data, bytes):
            return io.BytesIO(data)
        if isinstance(data, str):
            return io.StringIO(data)
        if isinstance(data, io.IOBase):
            return data

        raise TypeError(f'unsupported upload type: "{type(data)}"')

    @staticmethod
    def _decide_upload_type(force_resumable_upload: Optional[bool],
                            content_length: int) -> UploadType:
        # force resumable
        if force_resumable_upload is True:
            return UploadType.RESUMABLE

        # force simple
        if force_resumable_upload is False:
            return UploadType.SIMPLE

        # decide based on Content-Length
        if content_length > MAX_CONTENT_LENGTH_SIMPLE_UPLOAD:
            return UploadType.RESUMABLE

        return UploadType.SIMPLE

    @staticmethod
    def _split_content_type(content_type: str) -> Tuple[str, str]:
        content_type_and_encoding_split = content_type.split(';')
        content_type = content_type_and_encoding_split[0].lower().strip()

        encoding = None
        if len(content_type_and_encoding_split) > 1:
            encoding_str = content_type_and_encoding_split[1].lower().strip()
            encoding = encoding_str.split('=')[-1]

        return content_type, encoding

    async def _download(self, bucket: str, object_name: str, *,
                        params: dict = None, timeout: int = 10,
                        session: aiohttp.ClientSession = None) -> bytes:
        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        response = await session.get(url, headers=headers, params=params or {},
                                     timeout=timeout)
        response.raise_for_status()
        # N.B. the GCS API sometimes returns 'application/octet-stream' when a
        # string was uploaded. To avoid potential weirdness, always return a
        # bytes object.
        data: bytes = await response.read()
        return data

    async def _upload_simple(self, url: str, object_name: str,
                             stream: io.IOBase, headers: dict, *,
                             session: aiohttp.ClientSession = None,
                             timeout: int = 30) -> dict:
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/simple-upload
        params = {
            'name': object_name,
            'uploadType': 'media',
        }

        headers.update({
            'Accept': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=stream, headers=headers,
                                  params=params, timeout=timeout)
        resp.raise_for_status()
        data: dict = await resp.json()
        return data

    async def _upload_resumable(self, url: str, object_name: str,
                                stream: io.IOBase, headers: dict, *,
                                session: aiohttp.ClientSession = None,
                                timeout: int = 30) -> dict:
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/resumable-upload
        session_uri = await self._initiate_upload(url, object_name, headers,
                                                  session=session)
        data: dict = await self._do_upload(session_uri, stream,
                                           headers=headers, session=session,
                                           timeout=timeout)
        return data

    async def _initiate_upload(self, url: str, object_name: str, headers: dict,
                               *,
                               session: aiohttp.ClientSession = None) -> str:
        params = {
            'uploadType': 'resumable',
        }

        metadata = json.dumps({'name': object_name})

        post_headers = {**headers}
        post_headers.update({
            'Content-Length': str(len(metadata)),
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Type': headers['Content-Type'],
            'X-Upload-Content-Length': headers['Content-Length']
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, headers=post_headers, params=params,
                                  data=metadata, timeout=10)
        resp.raise_for_status()
        session_uri: str = resp.headers['Location']
        return session_uri

    async def _do_upload(self, session_uri: str, stream: io.IOBase,
                         headers: dict, *, retries: int = 5,
                         session: aiohttp.ClientSession = None,
                         timeout: int = 30) -> dict:
        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session

        resp = await session.put(session_uri, headers=headers, data=stream,
                                 timeout=timeout)
        for tries in range(retries):
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError:
                headers.update({'Content-Range': '*/*'})
                await asyncio.sleep(2. ** tries)

                resp = await session.put(session_uri, headers=headers,
                                         data=stream, timeout=timeout)
                continue

            break

        resp.raise_for_status()
        data: dict = await resp.json()
        return data
