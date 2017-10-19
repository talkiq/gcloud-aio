from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-bigquery').version

from gcloud.aio.bigquery.bigquery import make_stream_insert
from gcloud.aio.bigquery.bigquery import Table


__all__ = ['__version__', 'make_stream_insert', 'Table']
