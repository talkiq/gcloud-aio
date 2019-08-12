import io
import json
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import aiohttp

from .token import Token
from .token import Type
from .utils import encode


API_ROOT_IAM = 'https://iam.googleapis.com/v1'
API_ROOT_IAM_CREDENTIALS = 'https://iamcredentials.googleapis.com/v1'
SCOPES = ['https://www.googleapis.com/auth/iam']


class IamClient:
    def __init__(self, service_file: Optional[Union[str, io.IOBase]] = None,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        self.session = session
        self.token = token or Token(service_file=service_file,
                                    session=session, scopes=SCOPES)

        if self.token.token_type not in {Type.GCE_METADATA,
                                         Type.SERVICE_ACCOUNT}:
            raise TypeError('IAM Credentials Client is only valid for use '
                            'with Service Accounts or GCE Metadata')

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    @property
    def service_account_email(self) -> Optional[str]:
        return self.token.service_data.get('client_email')

    # https://cloud.google.com/iam/reference/rest/v1/projects.serviceAccounts.keys/get
    async def get_public_key(self, key_id: Optional[str] = None,
                             key: Optional[str] = None,
                             service_account_email: Optional[str] = None,
                             project: Optional[str] = None,
                             session: aiohttp.ClientSession = None,
                             timeout: int = 10) -> Dict[str, str]:
        service_account_email = (service_account_email
                                 or self.service_account_email)
        project = project or await self.token.get_project()

        if not key_id and not key:
            raise ValueError('get_public_key must have either key_id or key')

        if not key:
            key = (f'projects/{project}/serviceAccounts/'
                   f'{service_account_email}/keys/{key_id}')

        url = f'{API_ROOT_IAM}/{key}?publicKeyType=TYPE_X509_PEM_FILE'
        headers = await self.headers()

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/iam/reference/rest/v1/projects.serviceAccounts.keys/list
    async def list_public_keys(
            self, service_account_email: Optional[str] = None,
            project: Optional[str] = None,
            session: aiohttp.ClientSession = None,
            timeout: int = 10) -> List[Dict[str, str]]:
        service_account_email = (service_account_email
                                 or self.service_account_email)
        project = project or await self.token.get_project()

        url = (f'{API_ROOT_IAM}/projects/{project}/'
               f'serviceAccounts/{service_account_email}/keys')

        headers = await self.headers()

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return (await resp.json()).get('keys', [])

    # https://cloud.google.com/iam/credentials/reference/rest/v1/projects.serviceAccounts/signBlob
    async def sign_blob(self, payload: Optional[Union[str, bytes]],
                        service_account_email: Optional[str] = None,
                        delegates: Optional[list] = None,
                        session: aiohttp.ClientSession = None,
                        timeout: int = 10) -> Dict[str, str]:
        service_account_email = (service_account_email or
                                 self.service_account_email)
        if not service_account_email:
            raise TypeError('sign_blob must have a valid '
                            'service_account_email')

        resource_name = f'projects/-/serviceAccounts/{service_account_email}'
        url = f'{API_ROOT_IAM_CREDENTIALS}/{resource_name}:signBlob'

        json_str = json.dumps({
            'delegates': delegates or [resource_name],
            'payload': encode(payload).decode('utf-8'),
        })

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(json_str)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=json_str, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()
        return await resp.json()
