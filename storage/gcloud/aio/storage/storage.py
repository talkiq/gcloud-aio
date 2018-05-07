import logging

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.storage.bucket import Bucket
try:
    import ujson as json
except ModuleNotFoundError:
    import json


STORAGE_API_ROOT = 'https://www.googleapis.com/storage/v1/b'
STORAGE_UPLOAD_API_ROOT = 'https://www.googleapis.com/upload/storage/v1/b'
READ_WRITE_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_write'

log = logging.getLogger(__name__)


class Storage:
    def __init__(self, project, service_file, token=None, session=None):
        self.service_file = service_file

        self.session = session or aiohttp.ClientSession()
        self.token = token or Token(project, self.service_file,
                                    session=self.session,
                                    scopes=[READ_WRITE_SCOPE])

    async def download(self, bucket, object_name, params=None, session=None):
        token = await self.token.get()
        url = f'{STORAGE_API_ROOT}/{bucket}/o/{object_name}'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        session = session or self.session
        response = await session.get(url, headers=headers, params=params or {},
                                     timeout=60)
        content = await response.text()

        return response.status, content

    async def list_objects(self, bucket, params=None, session=None):
        token = await self.token.get()
        url = f'{STORAGE_API_ROOT}/{bucket}/o'
        headers = {
            'Authorization': f'Bearer {token}',
        }

        session = session or self.session
        response = await session.get(url, headers=headers, params=params or {},
                                     timeout=60)
        content = await response.json()

        return response.status, content

    async def upload(self, bucket, object_name, file_data, headers=None,
                     session=None):
        # pylint: disable=too-many-arguments
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/simple-upload
        token = await self.token.get()
        url = f'{STORAGE_UPLOAD_API_ROOT}/{bucket}/o'
        headers = headers or {}

        params = {
            'name': object_name,
            'uploadType': 'media',
        }

        if not isinstance(file_data, bytes):
            file_data = file_data.encode('utf-8')

        if file_data:
            file_data = json.dumps(file_data).encode('utf-8')
            content_length = str(len(file_data))
        else:
            content_length = '0'

        headers.update({
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}',
            'Content-Length': content_length,
            'Content-Type': 'application/json',
        })

        session = session or self.session
        response = await session.post(url, data=file_data, headers=headers,
                                      params=params, timeout=120)
        content = await response.json()

        return response.status, content

    async def download_as_string(self, bucket, object_name, session=None):
        object_name = object_name.replace('/', '%2F')

        _status, content = await self.download(bucket, object_name,
                                               params={'alt': 'media'},
                                               session=session)

        return content

    def get_bucket(self, bucket_name):
        return Bucket(self, bucket_name)
