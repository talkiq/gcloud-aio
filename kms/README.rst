(Asyncio OR Threadsafe) Python Client for Google Cloud KMS
==========================================================

    This is a shared codebase for ``gcloud-aio-kms`` and ``gcloud-rest-kms``

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-kms

Usage
-----

We're still working on more complete documentation, but roughly you can do:

.. code-block:: python

    from gcloud.aio.kms import KMS
    from gcloud.aio.kms import decode
    from gcloud.aio.kms import encode

    kms = KMS('my-kms-project', 'my-keyring', 'my-key-name')

    # encrypt
    plaintext = 'the-best-animal-is-the-aardvark'
    ciphertext = await kms.encrypt(encode(plaintext))

    # decrypt
    assert decode(await kms.decrypt(ciphertext)) == plaintext

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-kms.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-kms)
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-kms.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-kms)
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-kms.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-kms)
    :target: https://pypi.org/project/gcloud-rest-kms/
