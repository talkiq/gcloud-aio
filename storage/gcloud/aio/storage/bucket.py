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

        status, content = await self.storage.download(self.name, blob_name,
                                                      session=session)

        if status < 200 or status >= 300:
            log.error('Could not download %s/%s: %s', self.name, blob_name,
                      content)
            return

        content = json.loads(content)

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
