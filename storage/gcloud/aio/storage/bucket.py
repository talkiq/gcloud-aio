import logging
from typing import List

from gcloud.aio.auth import AioSession as RestSession  # pylint: disable=no-name-in-module

from .blob import Blob

try:
    from aiohttp import ClientResponseError as ResponseError
except ModuleNotFoundError:
    from requests import HTTPError as ResponseError

log = logging.getLogger(__name__)


class Bucket:
    def __init__(self, storage, name: str) -> None:
        self.storage = storage
        self.name = name

    async def get_blob(self, blob_name: str,
                       session: RestSession = None) -> Blob:
        metadata = await self.storage.download_metadata(self.name, blob_name,
                                                        session=session)

        return Blob(self, blob_name, metadata)

    async def blob_exists(self, blob_name: str,
                          session: RestSession = None) -> bool:
        try:
            await self.get_blob(blob_name, session=session)
            return True
        except ResponseError as e:
            if e.status in {404, 410}:
                return False
            raise e

    async def list_blobs(self, prefix: str = '',
                         session: RestSession = None) -> List[str]:
        params = {'prefix': prefix}
        content = await self.storage.list_objects(self.name, params=params,
                                                  session=session)

        return [x['name'] for x in content.get('items', list())]

    def new_blob(self, blob_name: str) -> Blob:
        return Blob(self, blob_name, {'size': 0})
