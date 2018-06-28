"""
An asynchronous client for Google Cloud KMS
"""
import aiohttp
from gcloud.aio.auth import Token


API_ROOT = 'https://cloudkms.googleapis.com/v1'
LOCATION = 'global'
SCOPES = [
    'https://www.googleapis.com/auth/cloudkms',
]


class KMS:
    def __init__(self, project, service_file, keyproject, keyring, keyname,
                 location=LOCATION, session=None, token=None):
        # pylint: disable=too-many-arguments
        self.session = session or aiohttp.ClientSession(conn_timeout=10,
                                                        read_timeout=10)

        self.api_root = (f'{API_ROOT}/projects/{keyproject}/'
                         f'locations/{location}/keyRings/{keyring}/'
                         f'cryptoKeys/{keyname}')

        self.token = token or Token(project, service_file, scopes=SCOPES,
                                    session=self.session)

    async def headers(self):
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/decrypt
    async def decrypt(self, ciphertext, session=None):
        url = f'{self.api_root}:decrypt'
        body = {
            'ciphertext': ciphertext,
        }

        s = session or self.session
        resp = await s.post(url, headers=await self.headers(), json=body)
        resp.raise_for_status()
        return (await resp.json())['plaintext']

    # https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/encrypt
    async def encrypt(self, plaintext, session=None):
        url = f'{self.api_root}:encrypt'
        body = {
            'plaintext': plaintext,
        }

        s = session or self.session
        resp = await s.post(url, headers=await self.headers(), json=body)
        resp.raise_for_status()
        return (await resp.json())['ciphertext']
