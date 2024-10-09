# pylint: disable=line-too-long
"""
This library implements various methods for working with the Google Bigquery
APIs.

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-bigquery

Usage
-----

We're still working on documentation -- for now, you can use the
`smoke test`_ as an example.

Emulators
---------

For testing purposes, you may want to use ``gcloud-aio-bigquery`` along with a
local emulator. Setting the ``$BIGQUERY_EMULATOR_HOST`` environment variable to
the address of your emulator should be enough to do the trick.

.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/bigquery/tests/integration/smoke_test.py
"""
import importlib.metadata

from .bigquery import Disposition
from .bigquery import SchemaUpdateOption
from .bigquery import SCOPES
from .bigquery import SourceFormat
from .dataset import Dataset
from .job import Job
from .table import Table
from .utils import query_response_to_dict


__version__ = importlib.metadata.version('gcloud-aio-bigquery')
__all__ = [
    'Dataset',
    'Disposition',
    'Job',
    'SCOPES',
    'SchemaUpdateOption',
    'SourceFormat',
    'Table',
    '__version__',
    'query_response_to_dict',
]
