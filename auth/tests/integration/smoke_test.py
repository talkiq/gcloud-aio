import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from gcloud.aio.auth import BUILD_GCLOUD_REST
from gcloud.aio.auth import decode
from gcloud.aio.auth import IamClient
from gcloud.aio.auth import Token

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio  # type: ignore
async def test_token_is_created(creds: str) -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    async with Session() as session:
        token = Token(service_file=creds, session=session, scopes=scopes)
        result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)


@pytest.mark.asyncio  # type: ignore
async def test_token_does_not_require_session(creds: str) -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    token = Token(service_file=creds, scopes=scopes)
    result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)


@pytest.mark.asyncio  # type: ignore
async def test_token_does_not_require_creds() -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    token = Token(scopes=scopes)
    result = await token.get()

    assert result
    assert token.access_token is not None
    assert token.access_token_duration != 0
    assert token.access_token_acquired_at != datetime.datetime(1970, 1, 1)


# Verification code adopted from (adapted to use cryptography lib):
# https://cloud.google.com/appengine/docs/standard/python/appidentity/#asserting_identity_to_third-party_services
async def verify_signature(data, signature, key_name, iam_client):
    key_data = await iam_client.get_public_key(key_name)
    cert = x509.load_pem_x509_certificate(decode(key_data['publicKeyData']),
                                          backend=default_backend())
    pubkey = cert.public_key()

    # raises on failure
    pubkey.verify(decode(signature), data.encode(), padding.PKCS1v15(),
                  hashes.SHA256())


@pytest.mark.asyncio  # type: ignore
async def test_sign_blob(creds: str) -> None:
    data = 'Testing Can be confidential!'

    async with Session(timeout=10) as s:
        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.sign_blob(data)
        signed_data = resp['signedBlob']
        await verify_signature(data, signed_data, resp['keyId'], iam_client)


@pytest.mark.asyncio  # type: ignore
async def test_get_service_account_public_key_names(creds: str) -> None:
    async with Session(timeout=10) as s:
        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.list_public_keys()
        assert len(resp) >= 1, '0 public keys found.'


@pytest.mark.asyncio  # type: ignore
async def test_get_service_account_public_key(creds: str) -> None:
    async with Session(timeout=10) as s:
        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.list_public_keys(session=s)
        pub_key_data = await iam_client.get_public_key(key=resp[0]['name'],
                                                       session=s)

        assert pub_key_data['name'] == resp[0]['name']
        assert 'publicKeyData' in pub_key_data

        key_id = resp[0]['name'].split('/')[-1]
        pub_key_by_key_id_data = await iam_client.get_public_key(key_id=key_id,
                                                                 session=s)

        # Sometimes, one or both keys will be created with "no" expiry.
        pub_key_time = pub_key_data.pop('validBeforeTime')
        pub_key_by_key_id_time = pub_key_by_key_id_data.pop('validBeforeTime')
        assert (pub_key_time == pub_key_by_key_id_time
                or '9999-12-31T23:59:59Z' in {pub_key_time,
                                              pub_key_by_key_id_time})

        assert pub_key_data == pub_key_by_key_id_data
