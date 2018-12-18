from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-datastore').version

from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import MoreResultsType
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.constants import ResultType
from gcloud.aio.datastore.datastore import Datastore
from gcloud.aio.datastore.entity import Entity
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.key import PathElement
from gcloud.aio.datastore.query import GQLQuery
from gcloud.aio.datastore.query import QueryResultBatch


__all__ = ['__version__', 'Consistency', 'Datastore', 'Entity', 'EntityResult',
           'GQLQuery', 'Key', 'Mode', 'MoreResultsType', 'Operation',
           'PathElement', 'QueryResultBatch', 'ResultType']
