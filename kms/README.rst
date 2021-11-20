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
    plaintext = b'the-best-animal-is-the-aardvark'
    ciphertext = await kms.encrypt(encode(plaintext))

    # decrypt
    assert decode(await kms.decrypt(ciphertext)) == plaintext

    # close the HTTP session
    # Note that other options include:
    # * providing your own session: ``KMS(.., session=session)``
    # * using a context manager: ``async with KMS(..) as kms:``
    await kms.close()

Emulators
~~~~~~~~~

For testing purposes, you may want to use ``gcloud-aio-kms`` along with a
local emulator. Setting the ``$KMS_EMULATOR_HOST`` environment variable
to the address of your emulator should be enough to do the trick.

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
