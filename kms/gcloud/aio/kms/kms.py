"""
An asynchronous client for Google Cloud KMS
"""
import io
from typing import Dict
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession as RestSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package

if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

API_ROOT = 'https://cloudkms.googleapis.com/v1'
LOCATION = 'global'
SCOPES = [
    'https://www.googleapis.com/auth/cloudkms',
]


class KMS:
    def __init__(self, keyproject: str, keyring: str, keyname: str,
                 service_file: Optional[Union[str, io.IOBase]] = None,
                 location: str = LOCATION, session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self.api_root = (f'{API_ROOT}/projects/{keyproject}/'
                         f'locations/{location}/keyRings/{keyring}/'
                         f'cryptoKeys/{keyname}')

        self.session = RestSession(session) if session else RestSession()
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=session)

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/decrypt
    async def decrypt(self, ciphertext: str,
                      session: Optional[Session] = None) -> str:
        url = f'{self.api_root}:decrypt'
        body = {
            'ciphertext': ciphertext,
        }

        s = RestSession(session) if session else self.session
        resp = await s.post(url, headers=await self.headers(), json=body)

        plaintext: str = (await resp.json())['plaintext']
        return plaintext

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/encrypt
    async def encrypt(self, plaintext: str,
                      session: Optional[Session] = None) -> str:
        url = f'{self.api_root}:encrypt'
        body = {
            'plaintext': plaintext,
        }

        s = RestSession(session) if session else self.session
        resp = await s.post(url, headers=await self.headers(), json=body)

        ciphertext: str = (await resp.json())['ciphertext']
        return ciphertext
