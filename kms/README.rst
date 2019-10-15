Asyncio Python Client for Google Cloud KMS
==========================================

|aio-pypi| |aio-pythons| |rest-pypi| |rest-pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-kms
    # or
    $ pip install --upgrade gcloud-rest-kms

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

.. |aio-pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-kms.svg?style=flat-square&label=pypi (aio)
    :alt: Latest PyPI Version (gcloud-aio-kms)
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |aio-pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-kms.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-kms)
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |rest-pypi| image:: https://img.shields.io/pypi/v/gcloud-rest-kms.svg?style=flat-square&label=pypi (rest)
    :alt: Latest PyPI Version (gcloud-rest-kms)
    :target: https://pypi.org/project/gcloud-rest-kms/

.. |rest-pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-kms.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-kms)
    :target: https://pypi.org/project/gcloud-rest-kms/
