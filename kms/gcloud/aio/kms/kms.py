"""
An asynchronous client for Google Cloud KMS
"""
import json
import os
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


API_ROOT = 'https://cloudkms.googleapis.com/v1'
LOCATION = 'global'
SCOPES = [
    'https://www.googleapis.com/auth/cloudkms',
]

KMS_EMULATOR_HOST = os.environ.get('KMS_EMULATOR_HOST')
if KMS_EMULATOR_HOST:
    API_ROOT = f'http://{KMS_EMULATOR_HOST}/v1'


class KMS:
    def __init__(self, keyproject: str, keyring: str, keyname: str,
                 service_file: Optional[Union[str, IO[AnyStr]]] = None,
                 location: str = LOCATION, session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self.api_root = (f'{API_ROOT}/projects/{keyproject}/'
                         f'locations/{location}/keyRings/{keyring}/'
                         f'cryptoKeys/{keyname}')

        self.session = AioSession(session)
        self.token = token or Token(
            service_file=service_file,
            session=self.session.session,  # type: ignore[arg-type]
            scopes=SCOPES)

    async def headers(self) -> Dict[str, str]:
        if KMS_EMULATOR_HOST:
            return {'Content-Type': 'application/json'}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/decrypt
    async def decrypt(self, ciphertext: str,
                      session: Optional[Session] = None) -> str:
        url = f'{self.api_root}:decrypt'
        body = json.dumps({
            'ciphertext': ciphertext,
        }).encode('utf-8')

        s = AioSession(session) if session else self.session
        # TODO: the type issue will be fixed in auth-4.0.2
        resp = await s.post(url, headers=await self.headers(),
                            data=body)  # type: ignore[arg-type]

        plaintext: str = (await resp.json())['plaintext']
        return plaintext

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/encrypt
    async def encrypt(self, plaintext: str,
                      session: Optional[Session] = None) -> str:
        url = f'{self.api_root}:encrypt'
        body = json.dumps({
            'plaintext': plaintext,
        }).encode('utf-8')

        s = AioSession(session) if session else self.session
        # TODO: the type issue will be fixed in auth-4.0.2
        resp = await s.post(url, headers=await self.headers(),
                            data=body)  # type: ignore[arg-type]

        ciphertext: str = (await resp.json())['ciphertext']
        return ciphertext

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'KMS':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
