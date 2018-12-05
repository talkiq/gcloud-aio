from typing import Any

import aiohttp


class Blob:
    def __init__(self, bucket, name: str, metadata: dict) -> None:
        self.__dict__.update(**metadata)

        self.bucket = bucket
        self.name = name
        self.size: int = int(self.size)

    @property
    def chunk_size(self) -> int:
        return self.size + (262144 - (self.size % 262144))

    async def download(self, session: aiohttp.ClientSession = None) -> Any:
        return await self.bucket.storage.download(self.bucket.name, self.name,
                                                  session=session)

    async def upload(self, data: Any,
                     session: aiohttp.ClientSession = None) -> dict:
        metadata: dict = await self.bucket.storage.upload(
            self.bucket.name, self.name, data, session=session)

        self.__dict__.update(metadata)
        return metadata
