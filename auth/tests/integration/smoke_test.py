import datetime

import aiohttp
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from gcloud.aio.auth import IamClient
from gcloud.aio.auth import Token
from gcloud.aio.auth.utils import encode


@pytest.mark.asyncio  # type: ignore
async def test_token_is_created(creds: str) -> None:
    scopes = ['https://www.googleapis.com/auth/taskqueue']

    async with aiohttp.ClientSession() as session:
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


# Verification code adopted from (adopted to use cryptography rather than pyCrypto):
# https://cloud.google.com/appengine/docs/standard/python/appidentity/#asserting_identity_to_third-party_services
async def verify_signature(data, signature, key_name, iam_client):
    key_data = await iam_client.get_public_key(key_name)
    pubkey = serialization.load_pem_public_key(key_data['publicKeyData'], backend=default_backend())
    try:
        pubkey.verify(signature, data, padding.PSS(mfg=padding.MGF1(hashes.SHA256()),
                                                   salt_length=padding.PSS.MAX_LENGTH),
                      hashes.SHA256())
        return True
    except InvalidSignature:
        return False


@pytest.mark.asyncio  # type: ignore
async def test_sign_blob(creds: str) -> None:
    data = 'Testing Can be confidential!'

    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:

        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.sign_blob(data)
        signed_data = resp['signedBlob']
        assert verify_signature(data, signed_data, resp['keyId'], iam_client)


@pytest.mark.asyncio  # type: ignore
async def test_get_service_account_public_key_names(creds: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.get_public_key_names()
        assert len(resp) > 1, 'There should be more than 1 public key retruned.'


@pytest.mark.asyncio  # type: ignore
async def test_get_service_account_public_key(creds: str) -> None:
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=10) as s:
        iam_client = IamClient(service_file=creds, session=s)
        resp = await iam_client.get_public_key_names(session=s)
        pub_key_data = await iam_client.get_public_key(key=resp[0]['name'], session=s)

        assert pub_key_data['name'] == resp[0]['name']
        assert 'publicKeyData' in pub_key_data

        key_id = resp[0]['name'].split('/')[-1]
        pub_key_by_key_id_data = await iam_client.get_public_key(key_id=key_id, session=s)
        assert pub_key_data == pub_key_by_key_id_data
