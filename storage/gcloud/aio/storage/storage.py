import enum
import io
import json
import logging
import mimetypes
import os
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union
from urllib.parse import quote

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.storage.bucket import Bucket

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from time import sleep
    from requests import HTTPError as ResponseError
    from requests import Session
else:
    from asyncio import sleep
    from aiohttp import ClientResponseError as ResponseError
    from aiohttp import ClientSession as Session


API_ROOT = 'https://www.googleapis.com/storage/v1/b'
API_ROOT_UPLOAD = 'https://www.googleapis.com/upload/storage/v1/b'
VERIFY_SSL = True
SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write',
]

MAX_CONTENT_LENGTH_SIMPLE_UPLOAD = 5 * 1024 * 1024  # 5 MB


STORAGE_EMULATOR_HOST = os.environ.get('STORAGE_EMULATOR_HOST')
if STORAGE_EMULATOR_HOST:
    API_ROOT = f'https://{STORAGE_EMULATOR_HOST}/storage/v1/b'
    API_ROOT_UPLOAD = 'https://{STORAGE_EMULATOR_HOST}/upload/storage/v1/b'
    VERIFY_SSL = False


log = logging.getLogger(__name__)


class UploadType(enum.Enum):
    SIMPLE = 1
    RESUMABLE = 2


class Storage:
    def __init__(self, *, service_file: Optional[Union[str, io.IOBase]] = None,
                 token: Optional[Token] = None,
                 session: Optional[Session] = None) -> None:
        self.session = AioSession(session, verify_ssl=VERIFY_SSL)
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session.session)

    def get_bucket(self, bucket_name: str) -> Bucket:
        return Bucket(self, bucket_name)

    async def copy(self, bucket: str, object_name: str,
                   destination_bucket: str, *, new_name: str = None,
                   headers: dict = None, params: dict = None,
                   timeout: int = 10,
                   session: Optional[Session] = None) -> bytes:

        """
        When files are too large, multiple calls to `rewriteTo` are made. We
        refer to the same copy job by using the `rewriteToken` from the
        previous return payload in subsequent `rewriteTo` calls.

        Using the `rewriteTo` GCS API is preferred in part because it is able
        to make multiple calls to fully copy an object whereas the `copyTo` GCS
        API only calls `rewriteTo` once under the hood, and thus may fail if
        files are large.

        In the rare case you need to resume a copy operation, include the
        `rewriteToken` in the `params` dictionary. Once you begin a multi-part
        copy operation, you then have 1 week to complete the copy job.

        https://cloud.google.com/storage/docs/json_api/v1/objects/rewrite
        """
        token = await self.token.get()

        if not new_name:
            new_name = object_name

        url = (f"{API_ROOT}/{bucket}/o/{quote(object_name, safe='')}/rewriteTo"
               f"/b/{destination_bucket}/o/{quote(new_name, safe='')}")

        # We may optionally supply metadata* to apply to the rewritten
        # object, which explains why `rewriteTo` is a POST endpoint; however,
        # we don't expose that here so we have to send an empty body. Therefore
        # the `Content-Length` and `Content-Type` indicate an empty body.
        #
        # * https://cloud.google.com/storage/docs/json_api/v1/objects#resource
        headers = headers or {}
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': '',
        })

        params = params or {}

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, params=params,
                            timeout=timeout)

        data: dict = await resp.json(content_type=None)

        while not data.get('done') and data.get('rewriteToken'):
            params['rewriteToken'] = data['rewriteToken']
            resp = await s.post(url, headers=headers, params=params,
                                timeout=timeout)
            data = await resp.json(content_type=None)

        return data

    async def delete(self, bucket: str, object_name: str, *,
                     params: dict = None, timeout: int = 10,
                     session: Optional[Session] = None) -> str:
        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        s = AioSession(session) if session else self.session
        resp = await s.delete(url, headers=headers, params=params or {},
                              timeout=timeout)

        try:
            data: str = await resp.text()
        except (AttributeError, TypeError):
            data: str = str(resp.text)

        return data

    async def download(self, bucket: str, object_name: str, *,
                       timeout: int = 10,
                       session: Optional[Session] = None) -> bytes:
        return await self._download(bucket, object_name, timeout=timeout,
                                    params={'alt': 'media'}, session=session)

    async def download_metadata(self, bucket: str, object_name: str, *,
                                timeout: int = 10,
                                session: Optional[Session] = None) -> dict:
        data = await self._download(bucket, object_name, timeout=timeout,
                                    session=session)
        metadata: dict = json.loads(data.decode())
        return metadata

    async def list_objects(self, bucket: str, *, params: dict = None,
                           session: Optional[Session] = None,
                           timeout: int = 10) -> dict:
        token = await self.token.get()
        url = f'{API_ROOT}/{bucket}/o'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params or {},
                           timeout=timeout)
        data: dict = await resp.json(content_type=None)
        return data

    # TODO: if `metadata` is set, use multipart upload:
    # https://cloud.google.com/storage/docs/json_api/v1/how-tos/upload
    # pylint: disable=too-many-locals
    async def upload(self, bucket: str, object_name: str, file_data: Any,
                     *, content_type: str = None, parameters: dict = None,
                     headers: dict = None, metadata: dict = None,
                     session: Optional[Session] = None, timeout: int = 30,
                     force_resumable_upload: bool = None) -> dict:
        token = await self.token.get()
        url = f'{API_ROOT_UPLOAD}/{bucket}/o'

        stream = self._preprocess_data(file_data)

        if BUILD_GCLOUD_REST and isinstance(stream, io.StringIO):
            # HACK: `requests` library does not accept `str` as `data` in `put`
            # HTTP request.
            stream = io.BytesIO(stream.getvalue().encode('utf-8'))

        content_length = self._get_stream_len(stream)

        # mime detection method same as in aiohttp 3.4.4
        content_type = content_type or mimetypes.guess_type(object_name)[0]

        parameters = parameters or {}

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
            if metadata:
                log.warning('metadata will be ignored for upload_type=Simple')
            return await self._upload_simple(url, object_name, stream,
                                             parameters, headers,
                                             session=session, timeout=timeout)

        if upload_type == UploadType.RESUMABLE:
            return await self._upload_resumable(
                url, object_name, stream, parameters, headers,
                metadata=metadata, session=session, timeout=timeout)

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
                        session: Optional[Session] = None) -> bytes:
        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        s = AioSession(session) if session else self.session
        response = await s.get(url, headers=headers, params=params or {},
                               timeout=timeout)
        # N.B. the GCS API sometimes returns 'application/octet-stream' when a
        # string was uploaded. To avoid potential weirdness, always return a
        # bytes object.
        try:
            data: bytes = await response.read()
        except (AttributeError, TypeError):
            data: bytes = response.content

        return data

    async def _upload_simple(self, url: str, object_name: str,
                             stream: io.IOBase, params: dict, headers: dict,
                             *, session: Optional[Session] = None,
                             timeout: int = 30) -> dict:
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/simple-upload
        params['name'] = object_name
        params['uploadType'] = 'media'

        headers.update({
            'Accept': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=stream, headers=headers, params=params,
                            timeout=timeout)
        data: dict = await resp.json(content_type=None)
        return data

    async def _upload_resumable(self, url: str, object_name: str,
                                stream: io.IOBase, params: dict,
                                headers: dict, *, metadata: dict = None,
                                session: Optional[Session] = None,
                                timeout: int = 30) -> dict:
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/resumable-upload
        session_uri = await self._initiate_upload(url, object_name, params,
                                                  headers, metadata=metadata,
                                                  session=session)
        data: dict = await self._do_upload(session_uri, stream,
                                           headers=headers, session=session,
                                           timeout=timeout)
        return data

    async def _initiate_upload(self, url: str, object_name: str, params: dict,
                               headers: dict, *, metadata: dict = None,
                               session: Optional[Session] = None) -> str:
        params['uploadType'] = 'resumable'

        metadict = (metadata or {}).copy()
        metadict.update({'name': object_name})
        metadata = json.dumps(metadict)

        post_headers = headers.copy()
        post_headers.update({
            'Content-Length': str(len(metadata)),
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Type': headers['Content-Type'],
            'X-Upload-Content-Length': headers['Content-Length']
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=post_headers, params=params,
                            data=metadata, timeout=10)
        session_uri: str = resp.headers['Location']
        return session_uri

    async def _do_upload(self, session_uri: str, stream: io.IOBase,
                         headers: dict, *, retries: int = 5,
                         session: Optional[Session] = None,
                         timeout: int = 30) -> dict:
        s = AioSession(session) if session else self.session

        for tries in range(retries):
            try:
                resp = await s.put(session_uri, headers=headers,
                                   data=stream, timeout=timeout)
            except ResponseError:
                headers.update({'Content-Range': '*/*'})
                await sleep(2. ** tries)

                continue

            break

        data: dict = await resp.json(content_type=None)
        return data

    async def get_bucket_metadata(self, bucket: str, *, params: dict = None,
                                  session: Optional[Session] = None,
                                  timeout: int = 10) -> dict:
        token = await self.token.get()
        url = f'{API_ROOT}/{bucket}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params or {},
                           timeout=timeout)
        data: dict = await resp.json(content_type=None)
        return data

    async def close(self):
        await self.session.close()

    async def __aenter__(self) -> 'Storage':
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
