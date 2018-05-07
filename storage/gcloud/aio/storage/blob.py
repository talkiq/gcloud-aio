try:
    import ujson as json
except ModuleNotFoundError:
    import json


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
            raise Exception(f'{status}: {json.dumps(content)}')

        self.__dict__.update(content)
        return content
