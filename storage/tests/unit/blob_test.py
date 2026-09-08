import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from gcloud.aio.storage import Blob


def generate_key(encoding_format):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=encoding_format,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return key, pem


@pytest.mark.parametrize(
    'encoding_format', [
        serialization.PrivateFormat.PKCS8,
        serialization.PrivateFormat.TraditionalOpenSSL,  # PKCS#1
    ],
)
def test_get_pem_signature(encoding_format):
    key, private_key = generate_key(encoding_format)

    signature = Blob.get_pem_signature('test-payload', private_key)

    key.public_key().verify(
        signature, b'test-payload', padding.PKCS1v15(), hashes.SHA256(),
    )


@pytest.mark.parametrize('private_key', ['', 'not a pem at all'])
def test_get_pem_signature_invalid_key(private_key):
    with pytest.raises(ValueError):
        Blob.get_pem_signature('test-payload', private_key)


def test_get_pem_signature_truncated_key():
    _, private_key = generate_key(serialization.PrivateFormat.PKCS8)
    lines = private_key.splitlines()
    truncated = '\n'.join(lines[:2] + lines[-1:]) + '\n'

    with pytest.raises(ValueError):
        Blob.get_pem_signature('test-payload', truncated)


def test_get_pem_signature_non_rsa_key():
    key = ec.generate_private_key(ec.SECP256R1())
    private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    with pytest.raises(ValueError):
        Blob.get_pem_signature('test-payload', private_key)
