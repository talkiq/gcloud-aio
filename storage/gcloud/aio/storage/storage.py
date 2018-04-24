import functools
import logging
import mimetypes

import aiohttp
import ujson
from gcloud.aio.auth import Token
from gcloud.aio.core.http import get
from gcloud.aio.core.http import HttpError
from gcloud.aio.core.http import post


STORAGE_API_ROOT = 'https://www.googleapis.com/storage/v1/b'
STORAGE_UPLOAD_API_ROOT = 'https://www.googleapis.com/upload/storage/v1/b'
READ_ONLY_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'
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


class Bucket:
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

    async def get_blob(self, blob_name, session=None):
        blob_name = blob_name.replace('/', '%2F')

        status, content = await self.storage.download(self.name, blob_name,
                                                      session=session)

        if status < 200 or status >= 300:
            log.error('Could not download %s/%s: %s', self.name, blob_name,
                      content)
            return

        content = ujson.loads(content)

        return Blob(self, blob_name, content)

    async def list_blobs(self, prefix='', session=None):
        params = {'prefix': prefix}

        status, content = await self.storage.list_objects(self.name,
                                                          params=params,
                                                          session=session)

        if status < 200 or status >= 300:
            log.error('Could not list %s/%s: %s', self.name, prefix, content)
            return

        return [x['name'] for x in content.get('items', list())]

    def new_blob(self, blob_name):
        return Blob(self, blob_name, {'size': 0})


class Blob:
    def __init__(self, bucket, name, data):
        self.__dict__.update(**data)

        self.bucket = bucket
        self.name = name
        self.size = int(self.size)

    @property
    def chunk_size(self):
        return self.size + (262144 - (self.size % 262144))

    async def download_as_string(self, session=None):
        return await self.bucket.storage.download_as_string(self.bucket.name,
                                                            self.name,
                                                            session=session)

    async def upload_from_string(self, data, session=None):
        status, content = await self.bucket.storage.upload(self.bucket.name,
                                                           self.name, data,
                                                           session=session)

        if status < 200 or status >= 300:
            raise HttpError('{}: {}'.format(status, ujson.dumps(content)))

        self.__dict__.update(content)
        return content


async def download(bucket, object_name):
    blob = await bucket.get_blob(object_name)
    if not blob:
        raise Exception('No such object "{}/{}"'.format(bucket.name,
                                                        object_name))

    return await blob.download_as_string()


def make_download(project, service_file, bucket_name, session=None,
                  token=None):
    token = token or Token(project, service_file, scopes=[READ_ONLY_SCOPE])

    storage = Storage(project, service_file, session=session, token=token)
    bucket = storage.get_bucket(bucket_name)

    return functools.partial(download, bucket)
