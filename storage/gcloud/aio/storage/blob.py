import binascii
import collections
import datetime
import hashlib
import io
from typing import Any
from typing import Optional
from typing import Union
from urllib.parse import quote

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import decode  # pylint: disable=no-name-in-module
from gcloud.aio.auth import IamClient  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


HOST = 'storage.googleapis.com'


class Blob:
    def __init__(self, bucket, name: str, metadata: dict) -> None:
        self.__dict__.update(**metadata)

        self.bucket = bucket
        self.name = name
        self.size: int = int(self.size)

    @property
    def chunk_size(self) -> int:
        return self.size + (262144 - (self.size % 262144))

    async def download(self, session: Optional[Session] = None) -> Any:
        return await self.bucket.storage.download(self.bucket.name, self.name,
                                                  session=session)

    async def upload(self, data: Any,
                     session: Optional[Session] = None) -> dict:
        metadata: dict = await self.bucket.storage.upload(
            self.bucket.name, self.name, data, session=session)

        self.__dict__.update(metadata)
        return metadata

    async def get_signed_url(  # pylint: disable=too-many-locals
            self, expiration: int, headers: Optional[dict] = None,
            query_params: Optional[dict] = None, http_method: str = 'GET',
            iam_client: Optional[IamClient] = None,
            service_account_email: Optional[str] = None,
            service_file: Optional[Union[str, io.IOBase]] = None,
            token: Optional[Token] = None,
            session: Optional[Session] = None) -> str:
        """
        Create a temporary access URL for Storage Blob accessible by anyone
        with the link.

        Adapted from Google Documentation:
        https://cloud.google.com/storage/docs/access-control/signing-urls-manually#python-sample
        """
        if expiration > 604800:
            raise ValueError("expiration time can't be longer than 604800 "
                             'seconds (7 days)')

        iam_client = iam_client or IamClient(service_file=service_file,
                                             token=token, session=session)

        quoted_name = quote(self.name, safe='')
        canonical_uri = f'/{self.bucket.name}/{quoted_name}'

        datetime_now = datetime.datetime.utcnow()
        request_timestamp = datetime_now.strftime('%Y%m%dT%H%M%SZ')
        datestamp = datetime_now.strftime('%Y%m%d')

        service_account_email = (service_account_email or
                                 iam_client.service_account_email)
        credential_scope = f'{datestamp}/auto/storage/goog4_request'
        credential = f'{service_account_email}/{credential_scope}'

        headers = headers or {}
        headers['host'] = HOST

        ordered_headers = collections.OrderedDict(sorted(headers.items()))
        canonical_headers = ''.join(
            f'{str(k).lower()}:{str(v).lower()}\n'
            for k, v in ordered_headers.items())

        signed_headers = ';'.join(
            f'{str(k).lower()}' for k in ordered_headers.keys())

        query_params = query_params or {}
        query_params['X-Goog-Algorithm'] = 'GOOG4-RSA-SHA256'
        query_params['X-Goog-Credential'] = credential
        query_params['X-Goog-Date'] = request_timestamp
        query_params['X-Goog-Expires'] = expiration
        query_params['X-Goog-SignedHeaders'] = signed_headers

        ordered_query_params = collections.OrderedDict(
            sorted(query_params.items()))

        canonical_query_str = '&'.join(
            f'{quote(str(k), safe="")}={quote(str(v), safe="")}'
            for k, v in ordered_query_params.items())

        canonical_req = '\n'.join([http_method, canonical_uri,
                                   canonical_query_str, canonical_headers,
                                   signed_headers, 'UNSIGNED-PAYLOAD'])
        canonical_req_hash = hashlib.sha256(canonical_req.encode()).hexdigest()

        str_to_sign = '\n'.join(['GOOG4-RSA-SHA256', request_timestamp,
                                 credential_scope, canonical_req_hash])
        signed_resp = await iam_client.sign_blob(
            str_to_sign, service_account_email=service_account_email,
            session=session)

        signature = binascii.hexlify(
            decode(signed_resp['signedBlob'])).decode()

        return (f'https://{HOST}{canonical_uri}?{canonical_query_str}'
                f'&X-Goog-Signature={signature}')
