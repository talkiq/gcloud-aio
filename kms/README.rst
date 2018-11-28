Asyncio Python Client for Google Cloud KMS
==========================================

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-kms

Usage
-----

We're still working on more complete documentation, but roughly you can do:

.. code-block:: python

    from gcloud.aio.kms import KMS
    from gcloud.aio.kms import decode
    from gcloud.aio.kms import encode

    kms = KMS('my-cred-project', '/path/to/creds.json', 'my-kms-project',
              'my-keyring', 'my-key-name')

    # encrypt
    plaintext = 'the-best-animal-is-the-aardvark'
    ciphertext = await kms.encrypt(encode(plaintext))

    # decrypt
    assert (await kms.decrypt(encode(ciphertext))) == plaintext

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-kms.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-kms.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-kms/
