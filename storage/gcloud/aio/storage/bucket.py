import logging
from gcloud.aio.storage.blob import Blob


log = logging.getLogger(__name__)


class Bucket:
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

    async def get_blob(self, blob_name, session=None):
        metadata = await self.storage.download_metadata(self.name, blob_name,
                                                        session=session)

        return Blob(self, blob_name, metadata)

    async def list_blobs(self, prefix='', session=None):
        params = {'prefix': prefix}
        content = await self.storage.list_objects(self.name, params=params,
                                                  session=session)

        return [x['name'] for x in content.get('items', list())]

    def new_blob(self, blob_name):
        return Blob(self, blob_name, {'size': 0})
