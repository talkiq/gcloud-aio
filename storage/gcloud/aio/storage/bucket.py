import logging

from gcloud.aio.storage.blob import Blob
try:
    import ujson as json
except ModuleNotFoundError:
    import json


log = logging.getLogger(__name__)


class Bucket:
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

    async def get_blob(self, blob_name, session=None):
        blob_name = blob_name.replace('/', '%2F')
        content = await self.storage.download(self.name, blob_name,
                                              session=session)

        return Blob(self, blob_name, json.loads(content))

    async def list_blobs(self, prefix='', session=None):
        params = {'prefix': prefix}
        content = await self.storage.list_objects(self.name, params=params,
                                                  session=session)

        return [x['name'] for x in content.get('items', list())]

    def new_blob(self, blob_name):
        return Blob(self, blob_name, {'size': 0})
