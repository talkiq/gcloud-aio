from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-bigquery').version

from gcloud.aio.bigquery.bigquery import Disposition
from gcloud.aio.bigquery.bigquery import SCOPES
from gcloud.aio.bigquery.bigquery import SourceFormat
from gcloud.aio.bigquery.bigquery import Table


__all__ = ['__version__', 'Disposition', 'SCOPES', 'SourceFormat', 'Table']
