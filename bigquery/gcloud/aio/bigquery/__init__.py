from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-bigquery').version

from gcloud.aio.bigquery.bigquery import Disposition
from gcloud.aio.bigquery.bigquery import SCOPES
from gcloud.aio.bigquery.bigquery import SchemaUpdateOption
from gcloud.aio.bigquery.bigquery import SourceFormat
from gcloud.aio.bigquery.dataset import Dataset
from gcloud.aio.bigquery.job import Job
from gcloud.aio.bigquery.table import Table
from gcloud.aio.bigquery.utils import query_response_to_dict


__all__ = [
    '__version__',
    'Dataset',
    'Disposition',
    'Job',
    'SCOPES',
    'SchemaUpdateOption',
    'SourceFormat',
    'Table',
    'query_response_to_dict',
]
