"""
An asynchronous client for Google Cloud KMS
"""
from typing import Dict
from typing import Optional

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module


API_ROOT = 'https://cloudkms.googleapis.com/v1'
LOCATION = 'global'
SCOPES = [
    'https://www.googleapis.com/auth/cloudkms',
]


class KMS:
    def __init__(self, keyproject: str, keyring: str, keyname: str,
                 service_file: Optional[str] = None, location: str = LOCATION,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        self.api_root = (f'{API_ROOT}/projects/{keyproject}/'
                         f'locations/{location}/keyRings/{keyring}/'
                         f'cryptoKeys/{keyname}')

        self.session = session
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session)

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/decrypt
    async def decrypt(self, ciphertext: str,
                      session: Optional[aiohttp.ClientSession] = None) -> str:
        url = f'{self.api_root}:decrypt'
        body = {
            'ciphertext': ciphertext,
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        s = session or self.session
        resp = await s.post(url, headers=await self.headers(), json=body)
        resp.raise_for_status()

        plaintext: str = (await resp.json())['plaintext']
        return plaintext

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/encrypt
    async def encrypt(self, plaintext: str,
                      session: Optional[aiohttp.ClientSession] = None) -> str:
        url = f'{self.api_root}:encrypt'
        body = {
            'plaintext': plaintext,
        }

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        s = session or self.session
        resp = await s.post(url, headers=await self.headers(), json=body)
        resp.raise_for_status()

        ciphertext: str = (await resp.json())['ciphertext']
        return ciphertext
