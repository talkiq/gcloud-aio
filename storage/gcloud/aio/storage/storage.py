import logging
import mimetypes

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.core.http import get
from gcloud.aio.core.http import post
from gcloud.aio.storage.bucket import Bucket


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
        session = session or self.session

        token = await self.token.get()
        url = '{}/{}/o/{}'.format(STORAGE_API_ROOT, bucket, object_name)
        headers = {
            'Authorization': 'Bearer {}'.format(token),
        }

        return await get(url, params=params or {}, headers=headers,
                         session=self.session, json_response=False)

    async def list_objects(self, bucket, params=None, session=None):
        session = session or self.session

        token = await self.token.get()
        url = '{}/{}/o'.format(STORAGE_API_ROOT, bucket)
        headers = {
            'Authorization': 'Bearer {}'.format(token),
        }

        return await get(url, params=params or {}, headers=headers,
                         session=self.session, json_response=True)

    async def upload(self, bucket, object_name, file_data, headers=None,
                     session=None):
        # pylint: disable=too-many-arguments
        # https://cloud.google.com/storage/docs/json_api/v1/how-tos/simple-upload
        session = session or self.session

        token = await self.token.get()
        url = '{}/{}/o'.format(STORAGE_UPLOAD_API_ROOT, bucket)
        headers = headers or {}

        # TODO: verify this
        if not isinstance(file_data, bytes):
            body = file_data.encode('utf-8')
        else:
            body = file_data

        body_length = str(len(body))

        params = {
            'name': object_name,
            'uploadType': 'media',
        }

        content_type = mimetypes.guess_type(object_name)[0]
        content_type = content_type or 'application/octet-stream'

        headers.update({
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(token),
            'Content-Length': body_length,
            'Content-Type': content_type,
        })

        return await post(url, params=params, payload=body, headers=headers,
                          timeout=120, session=session)

    async def download_as_string(self, bucket, object_name, session=None):
        object_name = object_name.replace('/', '%2F')

        _status, content = await self.download(bucket, object_name,
                                               params={'alt': 'media'},
                                               session=session)

        return content

    def get_bucket(self, bucket_name):
        return Bucket(self, bucket_name)
