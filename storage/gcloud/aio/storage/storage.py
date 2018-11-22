import logging
from urllib.parse import quote
import aiohttp
import asyncio
import mimetypes
from enum import Enum

from gcloud.aio.auth import Token
from gcloud.aio.storage.bucket import Bucket
try:
    import ujson as json
except ModuleNotFoundError:
    import json


STORAGE_API_ROOT = 'https://www.googleapis.com/storage/v1/b'
STORAGE_UPLOAD_API_ROOT = 'https://www.googleapis.com/upload/storage/v1/b'
READ_WRITE_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_write'

MAX_CONTENT_LENGTH_SIMPLE_UPLOAD = 5 * 1024 * 1024  # 5 MB


log = logging.getLogger(__name__)


class GcloudUploadType(Enum):
    SIMPLE = 1
    RESUMABLE = 2


class Storage:
    def __init__(self, project: str, service_file: str, token: str = None,
                 session: aiohttp.ClientSession = None):
        self.service_file = service_file
        self.session = session
        self.token = token or Token(project, self.service_file,
                                    session=self.session,
                                    scopes=[READ_WRITE_SCOPE])

    async def download(self, bucket: str, object_name: str,
                       session: aiohttp.ClientSession = None):
        return await self._download(bucket, object_name,
                                    params={'alt': 'media'}, session=session)

    async def download_metadata(self, bucket: str, object_name: str,
                                session: aiohttp.ClientSession = None):
        metadata_response = await self._download(bucket, object_name, session=session)
        metadata = json.loads(metadata_response)

        return metadata

    async def delete(self, bucket: str, object_name: str, params: dict = None,
                     session: aiohttp.ClientSession = None):
        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{STORAGE_API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.delete(url, headers=headers, params=params or {},
                                    timeout=60)
        resp.raise_for_status()
        return await resp.text()

    async def list_objects(self, bucket: str, params: dict = None, session: aiohttp.ClientSession = None):
        token = await self.token.get()
        url = f'{STORAGE_API_ROOT}/{bucket}/o'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.get(url, headers=headers, params=params or {},
                                 timeout=60)
        resp.raise_for_status()
        return await resp.json()

    async def upload(self, bucket: str, object_name: str,
                     file_data, headers=None, session: aiohttp.ClientSession = None,
                     content_type: str = None,
                     timeout: int = 120, force_resumable_upload: bool = None):
        def decide_upload_type(force_resumable_upload: bool, data_size: int) -> GcloudUploadType:

            if force_resumable_upload:
                upload_type: GcloudUploadType = GcloudUploadType.RESUMABLE
            elif not force_resumable_upload:
                upload_type: GcloudUploadType = GcloudUploadType.SIMPLE
            elif (force_resumable_upload is None) and (data_size > MAX_CONTENT_LENGTH_SIMPLE_UPLOAD):
                upload_type: GcloudUploadType = GcloudUploadType.RESUMABLE

            return upload_type

        token = await self.token.get()
        url = f'{STORAGE_UPLOAD_API_ROOT}/{bucket}/o'

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session

        data = self._preprocess_data(file_data)
        content_length = len(data)

        # mime detection method same as in aiohttp 3.4.4
        if content_type is None:
            content_type = mimetypes.guess_type(object_name)[0]

        headers = headers or {}
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Length': str(content_length),
            'Content-Type': content_type
        })

        upload_type = decide_upload_type(force_resumable_upload, len(data))
        log.debug(f'using {upload_type} gcloud storage upload method')
        if upload_type == GcloudUploadType.SIMPLE:
            return await self._upload_simple(url, bucket, object_name, data,
                                             headers=headers, session=session,
                                             timeout=timeout)
        elif upload_type == GcloudUploadType.RESUMABLE:
            return await self._upload_resumable(url, bucket, object_name, data,
                                                headers=headers, session=session,
                                                timeout=timeout)
        else:
            raise TypeError(f'upload type {upload_type} not supported')

    async def _upload_simple(self, url: str, bucket: str, object_name: str,
                             file_data, headers: dict = None,
                             session: aiohttp.ClientSession = None,
                             timeout: int = 120):
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
        resp = await session.post(url, data=file_data, headers=headers,
                                  params=params, timeout=120)
        resp.raise_for_status()
        return await resp.json()

    async def _upload_resumable(self, url: str, bucket: str, object_name: str,
                                data, headers: dict = None,
                                session: aiohttp.ClientSession = None, timeout: int = 120,
                                upload_type_resumable_always: bool = False):
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/resumable-upload
        async def initiate_upload_session(object_name: str, headers: dict, session: aiohttp.ClientSession):
            params = {
                'uploadType': 'resumable',
            }

            metadata = {'name': object_name}
            metadata_str = json.dumps(metadata)
            metadata_len = len(metadata_str)

            post_headers = {**headers}
            post_headers.update({
                'Content-Length': str(metadata_len),
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Upload-Content-Type': headers['Content-Type'],
                'X-Upload-Content-Length': headers['Content-Length']
            })

            resp = await session.post(url, headers=post_headers,
                                      params=params, data=metadata_str, timeout=5)
            resp.raise_for_status()
            session_URI = resp.headers['Location']

            return session_URI

        async def do_upload(session_URI: str, data, timeout: int,
                            headers: dict, session: aiohttp.ClientSession,
                            retries: int = 5, retry_sleep: float = 1.):
            tries = 0
            while True:
                resp = await session.put(session_URI, headers=headers, data=data, timeout=timeout)
                tries += 1
                if resp.status == 200:
                    break
                else:
                    headers.update({'Content-Range': '*/*'})
                    asyncio.sleep(retry_sleep)
                if tries > retries:
                    resp.raise_for_status()
                    break

            upload_response = await resp.json()

            return upload_response

        session_URI = await initiate_upload_session(object_name, headers, session)
        upload_response = await do_upload(session_URI, data, timeout, headers, session)

        return upload_response

    async def _download(self, bucket: str, object_name: str, params: dict = None,
                        session: aiohttp.ClientSession = None):

        def get_content_type_and_encoding(response_header: dict):
            content_type_and_encoding = response_header.get('Content-Type')
            content_type_and_encoding_split = content_type_and_encoding.split(
                ';')
            content_type = content_type_and_encoding_split[0].lower().strip()

            encoding = None
            if len(content_type_and_encoding_split) > 1:
                encoding_str = content_type_and_encoding_split[1].lower(
                ).strip()
                encoding = encoding_str.split('=')[-1]

            return (content_type, encoding)

        token = await self.token.get()
        # https://cloud.google.com/storage/docs/json_api/#encoding
        encoded_object_name = quote(object_name, safe='')
        url = f'{STORAGE_API_ROOT}/{bucket}/o/{encoded_object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        response = await session.get(url, headers=headers, params=params or {},
                                     timeout=60)
        response.raise_for_status()

        content_type, encoding = get_content_type_and_encoding(
            response.headers)

        if content_type == 'application/octet-stream':
            result = await response.read()
        elif content_type in ('text/plain', 'text/html', 'application/json'):
            result = await response.text(encoding)
        else:
            result = await response.read()

        return result

    def _preprocess_data(self, in_data):
        if in_data is None:
            return ''
        elif isinstance(in_data, (str, bytes)):
            return in_data
        else:
            raise TypeError(
                f'The type: "{type(in_data)}" of your input data is not supported.')

    def get_bucket(self, bucket_name: str):
        return Bucket(self, bucket_name)
