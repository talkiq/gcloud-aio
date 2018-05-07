import functools

from gcloud.aio.auth import Token
from gcloud.aio.storage.storage import Storage


READ_ONLY_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'


async def download(bucket, object_name):
    blob = await bucket.get_blob(object_name)
    if not blob:
        raise Exception(f'No such object "{bucket.name}/{object_name}"')

    return await blob.download_as_string()


def make_download(project, service_file, bucket_name, session=None,
                  token=None):
    token = token or Token(project, service_file, scopes=[READ_ONLY_SCOPE])

    storage = Storage(project, service_file, session=session, token=token)
    bucket = storage.get_bucket(bucket_name)

    return functools.partial(download, bucket)
