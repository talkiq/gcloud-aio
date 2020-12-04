from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-datastore').version

from gcloud.aio.datastore.constants import CompositeFilterOperator
from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Direction
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import MoreResultsType
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.constants import PropertyFilterOperator
from gcloud.aio.datastore.constants import ResultType
from gcloud.aio.datastore.datastore import Datastore
from gcloud.aio.datastore.datastore import SCOPES
from gcloud.aio.datastore.datastore_operation import DatastoreOperation
from gcloud.aio.datastore.entity import Entity
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.filter import CompositeFilter
from gcloud.aio.datastore.filter import Filter
from gcloud.aio.datastore.filter import PropertyFilter
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.key import PathElement
from gcloud.aio.datastore.lat_lng import LatLng
from gcloud.aio.datastore.mutation import MutationResult
from gcloud.aio.datastore.projection import Projection
from gcloud.aio.datastore.property_order import PropertyOrder
from gcloud.aio.datastore.query import GQLQuery
from gcloud.aio.datastore.query import Query
from gcloud.aio.datastore.query import QueryResultBatch
from gcloud.aio.datastore.value import Value


__all__ = ['__version__', 'CompositeFilter', 'CompositeFilterOperator',
           'Consistency', 'Datastore', 'DatastoreOperation', 'Direction',
           'Entity', 'EntityResult', 'Filter', 'GQLQuery', 'Key', 'LatLng',
           'Mode', 'MoreResultsType', 'MutationResult', 'Operation',
           'PathElement', 'Projection', 'PropertyFilter',
           'PropertyFilterOperator', 'PropertyOrder', 'Query',
           'QueryResultBatch', 'ResultType', 'SCOPES', 'Value']
