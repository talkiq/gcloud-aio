"""
Google Cloud auth via service account file
"""
import datetime
import enum
import json
import os
import time
from abc import ABCMeta
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Union
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse

import backoff
import cryptography  # pylint: disable=unused-import
import jwt

from .build_constants import BUILD_GCLOUD_REST
from .session import AioSession
# N.B. the cryptography library is required when calling jwt.encrypt() with
# algorithm='RS256'. It does not need to be imported here, but this allows us
# to throw this error at load time rather than lazily during normal operations,
# where plumbing this error through will require several changes to otherwise-
# good error handling.

# Handle differences in exceptions
try:
    # TODO: Type[Exception] should work here, no?
    CustomFileError: Any = FileNotFoundError
except NameError:
    CustomFileError = IOError


# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]
    import asyncio


GCE_METADATA_BASE = 'http://metadata.google.internal/computeMetadata/v1'
GCE_METADATA_HEADERS = {'metadata-flavor': 'Google'}
GCE_ENDPOINT_PROJECT = f'{GCE_METADATA_BASE}/project/project-id'
GCE_ENDPOINT_TOKEN = (
    f'{GCE_METADATA_BASE}/instance/service-accounts'
    '/default/token?recursive=true'
)
GCE_ENDPOINT_ID_TOKEN = (
    f'{GCE_METADATA_BASE}/instance/service-accounts'
    '/default/identity?audience={audience}&format=full'
)
GCLOUD_ENDPOINT_GENERATE_ACCESS_TOKEN = (
    'https://iamcredentials.googleapis.com'
    '/v1/projects/-/serviceAccounts/{service_account}:generateAccessToken'
)
GCLOUD_ENDPOINT_GENERATE_ID_TOKEN = (
    'https://iamcredentials.googleapis.com'
    '/v1/projects/-/serviceAccounts/{service_account}:generateIdToken'
)
REFRESH_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


class Type(enum.Enum):
    AUTHORIZED_USER = 'authorized_user'
    GCE_METADATA = 'gce_metadata'
    SERVICE_ACCOUNT = 'service_account'


def get_service_data(
        service: Optional[Union[str, IO[AnyStr]]],
) -> Dict[str, Any]:
    """
    Get the service data dictionary for the current auth method.

    This method is meant to match the official ``google.auth.default()``
    method (or rather, the subset relevant to our use-case). Things such as the
    precedence order of various approaches MUST be maintained. It was last
    updated to match the following commit:

    https://github.com/googleapis/google-auth-library-python/blob/6c1297c4d69ba40a8b9392775c17411253fcd73b/google/auth/_default.py#L504
    """
    # pylint: disable=too-complex
    # _get_explicit_environ_credentials()
    service = service or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not service:
        # _get_gcloud_sdk_credentials()
        cloudsdk_config = os.environ.get('CLOUDSDK_CONFIG')
        if cloudsdk_config is not None:
            sdkpath = cloudsdk_config
        elif os.name != 'nt':
            sdkpath = os.path.join(
                os.path.expanduser('~'), '.config',
                'gcloud',
            )
        else:
            try:
                sdkpath = os.path.join(os.environ['APPDATA'], 'gcloud')
            except KeyError:
                sdkpath = os.path.join(
                    os.environ.get('SystemDrive', 'C:'),
                    '\\', 'gcloud',
                )

        service = os.path.join(sdkpath, 'application_default_credentials.json')
        set_explicitly = bool(cloudsdk_config)
    else:
        set_explicitly = True

    # skip _get_gae_credentials(): this lib does not support GAEv1, and GAEv2
    # will fallback to the next step anyway.

    try:
        # also support passing IO objects directly rather than strictly paths
        # on disk
        try:
            with open(
                service,  # type: ignore[arg-type]
                encoding='utf-8',
            ) as f:
                data: Dict[str, Any] = json.loads(f.read())
                return data
        except TypeError:
            data = json.loads(service.read())  # type: ignore[union-attr]
            return data
    except CustomFileError:
        if set_explicitly:
            # only warn users if they have explicitly set the service_file
            # path, otherwise this is an expected code flow
            raise

        # _get_gce_credentials(): when we return {} here, the Token class falls
        # back to using the metadata service
        return {}
    except Exception:  # pylint: disable=broad-except
        return {}


@dataclass
class TokenResponse:
    value: str
    expires_in: int


class BaseToken:
    """GCP auth token base class."""
    # pylint: disable=too-many-instance-attributes
    __metaclass__ = ABCMeta

    def __init__(
        self, service_file: Optional[Union[str, IO[AnyStr]]] = None,
        session: Optional[Session] = None,
    ) -> None:
        self.service_data = get_service_data(service_file)
        if self.service_data:
            self.token_type = Type(self.service_data['type'])
            self.token_uri = self.service_data.get(
                'token_uri', 'https://oauth2.googleapis.com/token',
            )
        else:
            # At this point, all we can do is assume we're running somewhere
            # with default credentials, eg. GCE.
            self.token_type = Type.GCE_METADATA
            self.token_uri = GCE_ENDPOINT_TOKEN

        self.session = AioSession(session)

        self.access_token: Optional[str] = None
        self.access_token_duration = 0
        self.access_token_acquired_at = datetime.datetime(1970, 1, 1)

        self.acquiring: Optional['asyncio.Future[Any]'] = None

    async def get_project(self) -> Optional[str]:
        project = (
            os.environ.get('GOOGLE_CLOUD_PROJECT')
            or os.environ.get('GCLOUD_PROJECT')
            or os.environ.get('APPLICATION_ID')
        )
        if project:
            return project

        if self.token_type == Type.GCE_METADATA:
            await self.ensure_token()
            resp = await self.session.get(
                GCE_ENDPOINT_PROJECT, timeout=10,
                headers=GCE_METADATA_HEADERS,
            )

            try:
                return await resp.text()
            except (AttributeError, TypeError):
                return str(resp.text)

        if self.token_type == Type.SERVICE_ACCOUNT:
            return self.service_data.get('project_id')

        return None

    async def get(self) -> Optional[str]:
        await self.ensure_token()
        return self.access_token

    async def ensure_token(self) -> None:
        if self.acquiring and not self.acquiring.done():
            await self.acquiring
            return

        if self.access_token:
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = (now - self.access_token_acquired_at).total_seconds()
            if delta <= self.access_token_duration / 2:
                return

        self.acquiring = asyncio.ensure_future(  # pylint: disable=possibly-used-before-assignment
            self.acquire_access_token())
        await self.acquiring

    @abstractmethod
    async def refresh(self, *, timeout: int) -> TokenResponse:
        pass

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def acquire_access_token(self, timeout: int = 10) -> None:
        resp = await self.refresh(timeout=timeout)

        self.access_token = resp.value
        self.access_token_duration = resp.expires_in
        self.access_token_acquired_at = datetime.datetime.now(
            datetime.timezone.utc)
        self.acquiring = None

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'BaseToken':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class Token(BaseToken):
    """GCP OAuth 2.0 access token."""
    # pylint: disable=too-many-instance-attributes
    default_token_ttl = 3600

    def __init__(
        self, service_file: Optional[Union[str, IO[AnyStr]]] = None,
        session: Optional[Session] = None,
        scopes: Optional[List[str]] = None,
        target_principal: Optional[str] = None,
        delegates: Optional[List[str]] = None,
    ) -> None:
        super().__init__(service_file=service_file, session=session)

        self.scopes = ' '.join(scopes or [])
        if (self.token_type == Type.SERVICE_ACCOUNT
                or target_principal) and not self.scopes:
            raise Exception(
                'scopes must be provided when token type is '
                'service account or using target_principal',
            )
        self.target_principal = target_principal
        self.delegates = delegates

    async def _refresh_authorized_user(self, timeout: int) -> TokenResponse:
        payload = urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.service_data['client_id'],
            'client_secret': self.service_data['client_secret'],
            'refresh_token': self.service_data['refresh_token'],
        })

        resp = await self.session.post(
            url=self.token_uri, data=payload, headers=REFRESH_HEADERS,
            timeout=timeout,
        )
        content = await resp.json()
        return TokenResponse(value=str(content['access_token']),
                             expires_in=int(content['expires_in']))

    async def _refresh_gce_metadata(self, timeout: int) -> TokenResponse:
        resp = await self.session.get(
            url=self.token_uri, headers=GCE_METADATA_HEADERS, timeout=timeout,
        )
        content = await resp.json()
        return TokenResponse(value=str(content['access_token']),
                             expires_in=int(content['expires_in']))

    async def _refresh_service_account(self, timeout: int) -> TokenResponse:
        now = int(time.time())
        assertion_payload = {
            'aud': self.token_uri,
            'exp': now + self.default_token_ttl,
            'iat': now,
            'iss': self.service_data['client_email'],
            'scope': self.scopes,
        }

        # N.B. algorithm='RS256' requires an extra 240MB in dependencies...
        assertion = jwt.encode(
            assertion_payload,
            self.service_data['private_key'],
            algorithm='RS256',
        )
        payload = urlencode({
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        })

        resp = await self.session.post(
            self.token_uri, data=payload, headers=REFRESH_HEADERS,
            timeout=timeout,
        )
        content = await resp.json()
        return TokenResponse(value=str(content['access_token']),
                             expires_in=int(content['expires_in']))

    async def _impersonate(self, token: TokenResponse,
                           *, timeout: int) -> TokenResponse:
        # impersonate the target principal with optional delegates
        headers = {
            'Authorization': f'Bearer {token.value}',
        }
        payload = json.dumps({
            'lifetime': f'{self.default_token_ttl}s',
            'scope': self.scopes.split(' '),
            'delegates': self.delegates,
        })

        resp = await self.session.post(
            GCLOUD_ENDPOINT_GENERATE_ACCESS_TOKEN.format(
                service_account=self.target_principal),
            data=payload, headers=headers, timeout=timeout)

        data = await resp.json()
        token.value = str(data['accessToken'])
        return token

    async def refresh(self, *, timeout: int) -> TokenResponse:
        if self.token_type == Type.AUTHORIZED_USER:
            resp = await self._refresh_authorized_user(timeout=timeout)
        elif self.token_type == Type.GCE_METADATA:
            resp = await self._refresh_gce_metadata(timeout=timeout)
        elif self.token_type == Type.SERVICE_ACCOUNT:
            resp = await self._refresh_service_account(timeout=timeout)
        else:
            raise Exception(f'unsupported token type {self.token_type}')

        if self.target_principal:
            resp = await self._impersonate(resp, timeout=timeout)

        return resp


class IapToken(BaseToken):
    """An OpenID Connect ID token for a single IAP-secured service."""

    default_token_ttl = 3600

    def __init__(
        self, app_uri: str,
        service_file: Optional[Union[str, IO[AnyStr]]] = None,
        session: Optional[Session] = None,
        impersonating_service_account: Optional[str] = None,
    ) -> None:
        super().__init__(service_file=service_file, session=session)

        self.app_uri = app_uri
        self.service_account = impersonating_service_account

        if (self.token_type == Type.AUTHORIZED_USER
                and not self.service_account):
            raise Exception(
                'service account name must be provided when token type is '
                'authorized user',
            )

    async def _get_iap_client_id(self, *, timeout: int) -> str:
        """
        Fetch the IAP client ID from the service URI.

        If not logged in already, then we parse the OAuth redirect location to
        get the client ID. The redirect location is a header of the form:

            https://accounts.google.com/o/oauth2/v2/auth?client_id=<id>&...

        For more details, see the GCP docs for programmatic IAP access:
        https://cloud.google.com/iap/docs/authentication-howto
        """
        resp = await self.session.head(self.app_uri, timeout=timeout,
                                       allow_redirects=False)

        redirect_location = resp.headers.get('location')
        if not redirect_location:
            raise Exception(f'No redirect location for service {self.app_uri},'
                            ' is it secured with IAP?')

        parsed_uri = urlparse(redirect_location)
        query = parse_qs(parsed_uri.query)
        client_id: str = query.get('client_id', [''])[0]
        if not client_id:
            raise Exception(f'No client ID found for service {self.app_uri},'
                            ' is it secured with IAP?')
        return client_id

    async def _refresh_authorized_user(
        self, iap_client_id: str,
        timeout: int,
    ) -> TokenResponse:
        """
        Fetch IAP ID token by impersonating a service account.

        https://cloud.google.com/iap/docs/authentication-howto#obtaining_an_oidc_token_in_all_other_cases
        """
        # Fetch the OAuth access token to use in generating an ID token.
        refresh_payload = urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.service_data['client_id'],
            'client_secret': self.service_data['client_secret'],
            'refresh_token': self.service_data['refresh_token'],
        })
        refresh_resp = await self.session.post(
            url=self.token_uri, data=refresh_payload, headers=REFRESH_HEADERS,
            timeout=timeout,
        )
        refresh_content = await refresh_resp.json()

        headers = {
            'Authorization': f'Bearer {refresh_content["access_token"]}',
        }
        payload = json.dumps({
            'includeEmail': True,
            'audience': iap_client_id,
        })
        resp = await self.session.post(
            GCLOUD_ENDPOINT_GENERATE_ID_TOKEN.format(
                service_account=self.service_account),
            data=payload, headers=headers, timeout=timeout)

        content = await resp.json()
        return TokenResponse(value=content['token'],
                             expires_in=self.default_token_ttl)

    async def _refresh_gce_metadata(
            self, iap_client_id: str,
            timeout: int,
    ) -> TokenResponse:
        """
        Fetch IAP ID token from the GCE metadata servers.

        Note: The official documentation states that the URI be used for the
        audience but this is not the case. The typical audience value must be
        used as in other flavours of ID token fetching.

        https://cloud.google.com/docs/authentication/get-id-token#metadata-server
        """
        resp = await self.session.get(
            GCE_ENDPOINT_ID_TOKEN.format(audience=iap_client_id),
            headers=GCE_METADATA_HEADERS, timeout=timeout)
        try:
            token = await resp.text()  # aiohttp lib
        except (AttributeError, TypeError):
            token = str(resp.text)  # requests lib
        return TokenResponse(value=token,
                             expires_in=self.default_token_ttl)

    async def _refresh_service_account(
        self, iap_client_id: str,
        timeout: int,
    ) -> TokenResponse:
        now = int(time.time())
        expiry = now + self.default_token_ttl

        assertion_payload = {
            'iss': self.service_data['client_email'],
            'aud': self.token_uri,
            'exp': expiry,
            'iat': now,
            'sub': self.service_data['client_email'],
            'target_audience': iap_client_id,
        }

        assertion = jwt.encode(
            assertion_payload,
            self.service_data['private_key'],
            algorithm='RS256',
        )

        payload = urlencode({
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        })

        resp = await self.session.post(self.token_uri, data=payload,
                                       headers=REFRESH_HEADERS,
                                       timeout=timeout)

        content = await resp.json()
        return TokenResponse(value=content['id_token'],
                             expires_in=expiry - int(time.time()))

    async def refresh(self, *, timeout: int) -> TokenResponse:
        iap_client_id = await self._get_iap_client_id(timeout=timeout)
        if self.token_type == Type.AUTHORIZED_USER:
            resp = await self._refresh_authorized_user(
                iap_client_id, timeout)
        elif self.token_type == Type.GCE_METADATA:
            resp = await self._refresh_gce_metadata(
                iap_client_id, timeout)
        elif self.token_type == Type.SERVICE_ACCOUNT:
            resp = await self._refresh_service_account(
                iap_client_id, timeout)
        else:
            raise Exception(f'unsupported token type {self.token_type}')

        return resp
