import binascii
import collections
import datetime
import enum
import hashlib
import io
from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING
from urllib.parse import quote

import rsa
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import decode  # pylint: disable=no-name-in-module
from gcloud.aio.auth import IamClient  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from pyasn1.codec.der import decoder
from pyasn1_modules import pem
from pyasn1_modules.rfc5208 import PrivateKeyInfo

from .constants import DEFAULT_TIMEOUT

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]

if TYPE_CHECKING:
    from .bucket import Bucket  # pylint: disable=cyclic-import


HOST = 'storage.googleapis.com'

PKCS1_MARKER = (
    '-----BEGIN RSA PRIVATE KEY-----',
    '-----END RSA PRIVATE KEY-----',
)
PKCS8_MARKER = (
    '-----BEGIN PRIVATE KEY-----',
    '-----END PRIVATE KEY-----',
)
PKCS8_SPEC = PrivateKeyInfo()


class PemKind(enum.Enum):
    """
    Tracks the response of ``pem.readPemBlocksFromFile(key, *args)``>

    Note that the specified method returns ``(marker_id, key_bytes)``, where
    ``marker_id`` is the integer index of the matching ``arg`` (or -1 if no
    match was found.

    For example::

        (marker_id, _) = pem.readPemBlocksFromFile(key, PKCS1_MARKER,
                                                   PCKS8_MARKER)
        if marker_id == -1:
            # "key" did not match either type or was invalid
        if marker_id == 0:
            # "key" matched the zeroth provided marker arg, eg. PKCS1_MARKER
        if marker_id == 1:
            # "key" matched the zeroth provided marker arg, eg. PKCS8_MARKER
    """

    INVALID = -1
    PKCS1 = 0
    PKCS8 = 1


class _SignatureMethod(enum.Enum):
    """
    Indicates where the url signing will be done through Google's
    IAM API or through local signing with a PEM file, which is faster
    but requires that the provided token contains client_email and
    private_key data
    """

    PEM = 0
    IAM_API = 1


class Blob:
    def __init__(
        self, bucket: 'Bucket', name: str,
        metadata: Dict[str, Any],
    ) -> None:
        self.__dict__.update(**metadata)

        self.bucket = bucket
        self.name = name
        self.size: int = int(self.size)

    @property
    def chunk_size(self) -> int:
        return self.size + (262144 - (self.size % 262144))

    async def download(
        self, timeout: int = DEFAULT_TIMEOUT,
        session: Optional[Session] = None,
        auto_decompress: bool = True,
    ) -> Any:
        headers = None if auto_decompress else {'accept-encoding': 'gzip'}
        return await self.bucket.storage.download(
            self.bucket.name,
            self.name,
            timeout=timeout,
            session=session,
            headers=headers,
        )

    async def upload(
        self, data: Any,
        content_type: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        metadata = await self.bucket.storage.upload(
            self.bucket.name,
            self.name,
            data,
            content_type=content_type,
            session=session,
        )

        self.__dict__.update(metadata)
        return metadata

    async def get_signed_url(  # pylint: disable=too-many-locals
            self, expiration: int, headers: Optional[Dict[str, str]] = None,
            query_params: Optional[Dict[str, Any]] = None,
            http_method: str = 'GET', iam_client: Optional[IamClient] = None,
            service_account_email: Optional[str] = None,
            token: Optional[Token] = None, session: Optional[Session] = None,
    ) -> str:
        """
        Create a temporary access URL for Storage Blob accessible by anyone
        with the link.

        Adapted from Google Documentation:
        https://cloud.google.com/storage/docs/access-control/signing-urls-manually#python-sample
        """
        if expiration > 604800:
            raise ValueError(
                "expiration time can't be longer than 604800 "
                'seconds (7 days)',
            )

        quoted_name = quote(self.name, safe=b'/~')
        canonical_uri = f'/{self.bucket.name}/{quoted_name}'

        datetime_now = datetime.datetime.now(datetime.timezone.utc)
        request_timestamp = datetime_now.strftime('%Y%m%dT%H%M%SZ')
        datestamp = datetime_now.strftime('%Y%m%d')

        token = token or self.bucket.storage.token
        credential_scope = f'{datestamp}/auto/storage/goog4_request'
        # Try to sign locally if available
        client_email = token.service_data.get('client_email')
        private_key = token.service_data.get('private_key')
        if not client_email or not private_key:
            # Cannot sign locally, so we'll have to use Google's IAM API
            signature_method = _SignatureMethod.IAM_API
            credential = f'{service_account_email}/{credential_scope}'
        else:
            signature_method = _SignatureMethod.PEM
            credential = f'{client_email}/{credential_scope}'

        headers = headers or {}
        headers['host'] = HOST

        ordered_headers = collections.OrderedDict(
            sorted(headers.items(), key=lambda x: x[0].lower()))
        canonical_headers = ''.join(
            f'{str(k).lower()}:{str(v).lower()}\n'
            for k, v in ordered_headers.items()
        )

        signed_headers = ';'.join(
            f'{str(k).lower()}' for k in ordered_headers.keys()
        )

        query_params = query_params or {}
        query_params['X-Goog-Algorithm'] = 'GOOG4-RSA-SHA256'
        query_params['X-Goog-Credential'] = credential
        query_params['X-Goog-Date'] = request_timestamp
        query_params['X-Goog-Expires'] = expiration
        query_params['X-Goog-SignedHeaders'] = signed_headers

        ordered_query_params = collections.OrderedDict(
            sorted(query_params.items()),
        )

        canonical_query_str = '&'.join(
            f'{quote(str(k), safe="")}={quote(str(v), safe="")}'
            for k, v in ordered_query_params.items()
        )

        canonical_req = '\n'.join([
            http_method, canonical_uri,
            canonical_query_str, canonical_headers,
            signed_headers, 'UNSIGNED-PAYLOAD',
        ])
        canonical_req_hash = hashlib.sha256(canonical_req.encode()).hexdigest()

        str_to_sign = '\n'.join([
            'GOOG4-RSA-SHA256', request_timestamp,
            credential_scope, canonical_req_hash,
        ])

        if (signature_method == _SignatureMethod.PEM and private_key
                and isinstance(private_key, str)):
            signed_blob = self.get_pem_signature(str_to_sign, private_key)
        else:
            try:
                iam_client = iam_client or IamClient(
                    token=token, session=session)
            except TypeError as e:
                raise TypeError('Blob signing is not yet supported'
                                ' for AUTHORIZED_USER tokens') from e
            signed_blob = await self.get_iam_api_signature(
                str_to_sign,
                iam_client,
                service_account_email,
                session,
            )

        signature = binascii.hexlify(signed_blob).decode()

        return (
            f'https://{HOST}{canonical_uri}?'
            f'{canonical_query_str}&X-Goog-Signature={signature}'
        )

    @staticmethod
    def get_pem_signature(str_to_sign: str, private_key: str) -> bytes:
        # N.B. see the ``PemKind`` enum
        marker_id, key_bytes = pem.readPemBlocksFromFile(
            io.StringIO(private_key), PKCS1_MARKER, PKCS8_MARKER,
        )
        if marker_id == PemKind.INVALID.value:
            raise ValueError('private key is invalid or unsupported')

        if marker_id == PemKind.PKCS8.value:
            # convert from pkcs8 to pkcs1
            key_info, remaining = decoder.decode(
                key_bytes,
                asn1Spec=PKCS8_SPEC,
            )
            if remaining != b'':
                raise ValueError(
                    'could not read PKCS8 key: found extra bytes',
                    remaining,
                )

            private_key_info = key_info.getComponentByName('privateKey')
            key_bytes = private_key_info.asOctets()

        key = rsa.key.PrivateKey.load_pkcs1(key_bytes, format='DER')
        signed_blob = rsa.pkcs1.sign(
            str_to_sign.encode(),
            key,
            'SHA-256',
        )
        return signed_blob

    @staticmethod
    async def get_iam_api_signature(
            str_to_sign: str, iam_client: IamClient,
            service_account_email: Optional[str], session: Optional[Session],
    ) -> bytes:
        signed_resp = await iam_client.sign_blob(
            str_to_sign,
            service_account_email=service_account_email,
            session=session,
        )
        return decode(signed_resp['signedBlob'])
