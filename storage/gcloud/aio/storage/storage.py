import logging
from urllib.parse import quote

import aiohttp
import asyncio

from gcloud.aio.auth import Token
from gcloud.aio.storage.bucket import Bucket
try:
    import ujson as json
except ModuleNotFoundError:
    import json


STORAGE_API_ROOT = 'https://www.googleapis.com/storage/v1/b'
STORAGE_UPLOAD_API_ROOT = 'https://www.googleapis.com/upload/storage/v1/b'
READ_WRITE_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_write'

MAX_CONTENT_LENGTH_SIMPLE_UPLOAD = 5242880  # 5 MB


log = logging.getLogger(__name__)


class Storage:
    def __init__(self, project, service_file, token=None, session=None):
        self.service_file = service_file

        self.session = session
        self.token = token or Token(project, self.service_file,
                                    session=self.session,
                                    scopes=[READ_WRITE_SCOPE])

    async def download(self, bucket, object_name, params=None, session=None):
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
        resp = await session.get(url, headers=headers, params=params or {},
                                 timeout=60)
        resp.raise_for_status()
        return await resp.text()

    async def delete(self, bucket, object_name, params=None, session=None):
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

    async def list_objects(self, bucket, params=None, session=None):
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
                     file_data, content_type: str,
                     headers=None, session: aiohttp.ClientSession = None,
                     timeout: int = 120, upload_type_resumable_always: bool = False):
        token = await self.token.get()
        url = f'{STORAGE_UPLOAD_API_ROOT}/{bucket}/o'

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session

        data = self.preprocess_data_(file_data)
        content_length = len(data)

        headers = headers or {}
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Length': str(content_length),
            'Content-Type': content_type
        })

        if len(file_data) > MAX_CONTENT_LENGTH_SIMPLE_UPLOAD or upload_type_resumable_always:
            response = await self._upload_resumable(url, bucket, object_name, file_data,
                                                    headers=headers, session=session, timeout=timeout)
        else:
            response = await self._upload_simple(url, bucket, object_name, file_data,
                                                 content_type, headers=headers, session=session,
                                                 timeout=timeout)

        return response

    async def _upload_simple(self, url: str, bucket: str, object_name: str,
                             file_data, content_type: str,
                             headers: dict = None, session: aiohttp.ClientSession = None,
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

            resp = await session.post(url, headers=post_headers, params=params, data=metadata_str, timeout=5)
            resp.raise_for_status()

            header_with_session_URI = dict(resp.headers)
            session_URI = header_with_session_URI.get('Location')
            if not session_URI:
                raise RuntimeError('Not able to initiate resumable upload session -- no URI in response header')

            return session_URI

        async def do_upload(session_URI: str, data, timeout: int,
                            headers: dict, session: aiohttp.ClientSession,
                            retries=5, retry_sleep=1.):
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

    def preprocess_data_(self, in_data):
        if in_data is None:
            out_data = ''
        elif isinstance(in_data, str) or isinstance(in_data, bytes):
            out_data = in_data
        else:
            raise RuntimeError('Currently, str and bytes -- exiting')
        return out_data

    def get_bucket(self, bucket_name):
        return Bucket(self, bucket_name)
