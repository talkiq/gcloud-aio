import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module

from .blob import Blob
from .constants import DEFAULT_TIMEOUT

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import HTTPError as ResponseError
    from requests import Session
else:
    from aiohttp import (  # type: ignore[assignment]
        ClientResponseError as ResponseError,
    )
    from aiohttp import ClientSession as Session  # type: ignore[assignment]

if TYPE_CHECKING:
    from .storage import Storage  # pylint: disable=cyclic-import


log = logging.getLogger(__name__)


class Bucket:
    def __init__(self, storage: 'Storage', name: str) -> None:
        self.storage = storage
        self.name = name

    async def get_blob(
        self, blob_name: str, timeout: int = DEFAULT_TIMEOUT,
        session: Optional[Session] = None,
    ) -> Blob:
        metadata = await self.storage.download_metadata(
            self.name, blob_name,
            timeout=timeout,
            session=session,
        )

        return Blob(self, blob_name, metadata)

    async def blob_exists(
        self, blob_name: str,
        session: Optional[Session] = None,
    ) -> bool:
        try:
            await self.get_blob(blob_name, session=session)
            return True
        except ResponseError as e:
            try:
                if e.status in {404, 410}:  # type: ignore[attr-defined]
                    return False
            except AttributeError:
                if e.code in {404, 410}:  # type: ignore[attr-defined]
                    return False

            raise e

    async def list_blobs(
        self, prefix: str = '', match_glob: str = '',
        session: Optional[Session] = None,
    ) -> List[str]:
        params = {'prefix': prefix, 'matchGlob': match_glob, 'pageToken': ''}
        items = []
        while True:
            content = await self.storage.list_objects(
                self.name,
                params=params,
                session=session,
            )
            items.extend([x['name'] for x in content.get('items', [])])

            params['pageToken'] = content.get('nextPageToken', '')
            if not params['pageToken']:
                break

        return items

    def new_blob(self, blob_name: str) -> Blob:
        return Blob(self, blob_name, {'size': 0})

    async def get_metadata(
            self, params: Optional[Dict[str, Any]] = None,
            session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return await self.storage.get_bucket_metadata(
            self.name, params=params,
            session=session,
        )
