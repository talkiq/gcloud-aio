import json
import logging
import os
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.datastore_operation import DatastoreOperation
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.mutation import MutationResult
from gcloud.aio.datastore.query import BaseQuery
from gcloud.aio.datastore.query import QueryResultBatch
from gcloud.aio.datastore.value import Value

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


# TODO: is cloud-platform needed?
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/datastore',
]

log = logging.getLogger(__name__)


def init_api_root(api_root: Optional[str]) -> Tuple[bool, str]:
    if api_root:
        return True, api_root

    host = os.environ.get('DATASTORE_EMULATOR_HOST')
    if host:
        return True, f'http://{host}/v1'

    return False, 'https://datastore.googleapis.com/v1'


class Datastore:
    datastore_operation_kind = DatastoreOperation
    entity_result_kind = EntityResult
    key_kind = Key
    mutation_result_kind = MutationResult
    query_result_batch_kind = QueryResultBatch
    value_kind = Value

    _project: Optional[str]
    _api_root: str
    _api_is_dev: bool

    def __init__(
            self, project: Optional[str] = None,
            service_file: Optional[Union[str, IO[AnyStr]]] = None,
            namespace: str = '', session: Optional[Session] = None,
            token: Optional[Token] = None, api_root: Optional[str] = None,
    ) -> None:
        self._api_is_dev, self._api_root = init_api_root(api_root)
        self.namespace = namespace
        self.session = AioSession(session)
        self.token = token or Token(
            service_file=service_file, scopes=SCOPES,
            session=self.session.session,  # type: ignore[arg-type]
        )

        self._project = project
        if self._api_is_dev and not project:
            self._project = (
                os.environ.get('DATASTORE_PROJECT_ID')
                or os.environ.get('GOOGLE_CLOUD_PROJECT')
                or 'dev'
            )

    async def project(self) -> str:
        if self._project:
            return self._project

        self._project = await self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    @staticmethod
    def _make_commit_body(
        mutations: List[Dict[str, Any]],
        transaction: Optional[str] = None,
        mode: Mode = Mode.TRANSACTIONAL,
    ) -> Dict[str, Any]:
        if not mutations:
            raise Exception('at least one mutation record is required')

        if transaction is None and mode != Mode.NON_TRANSACTIONAL:
            raise Exception(
                'a transaction ID must be provided when mode is '
                'transactional',
            )

        data = {
            'mode': mode.value,
            'mutations': mutations,
        }
        if transaction is not None:
            data['transaction'] = transaction
        return data

    async def headers(self) -> Dict[str, str]:
        if self._api_is_dev:
            return {}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    # TODO: support mutations w version specifiers, return new version (commit)
    @classmethod
    def make_mutation(
            cls, operation: Operation, key: Key,
            properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if operation == Operation.DELETE:
            return {operation.value: key.to_repr()}

        mutation_properties = {}
        for k, v in (properties or {}).items():
            value = v if isinstance(v, cls.value_kind) else cls.value_kind(v)
            mutation_properties[k] = value.to_repr()

        return {
            operation.value: {
                'key': key.to_repr(),
                'properties': mutation_properties,
            },
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/allocateIds
    async def allocateIds(
        self, keys: List[Key],
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> List[Key]:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:allocateIds'

        payload = json.dumps({
            'keys': [k.to_repr() for k in keys],
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )
        data = await resp.json()

        return [self.key_kind.from_repr(k) for k in data['keys']]

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/beginTransaction
    # TODO: support readwrite vs readonly transaction types
    async def beginTransaction(
        self, session: Optional[Session] = None,
        timeout: int = 10,
    ) -> str:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:beginTransaction'
        headers = await self.headers()
        headers.update({
            'Content-Length': '0',
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, timeout=timeout)
        data = await resp.json()

        transaction: str = data['transaction']
        return transaction

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit
    async def commit(
        self, mutations: List[Dict[str, Any]],
        transaction: Optional[str] = None,
        mode: Mode = Mode.TRANSACTIONAL,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:commit'

        body = self._make_commit_body(
            mutations, transaction=transaction,
            mode=mode,
        )
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )
        data: Dict[str, Any] = await resp.json()

        return {
            'mutationResults': [
                self.mutation_result_kind.from_repr(r)
                for r in data.get('mutationResults', [])
            ],
            'indexUpdates': data.get('indexUpdates', 0),
        }

    # https://cloud.google.com/datastore/docs/reference/admin/rest/v1/projects/export
    async def export(
        self, output_bucket_prefix: str,
        kinds: Optional[List[str]] = None,
        namespaces: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> DatastoreOperation:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:export'

        payload = json.dumps({
            'entityFilter': {
                'kinds': kinds or [],
                'namespaceIds': namespaces or [],
            },
            'labels': labels or {},
            'outputUrlPrefix': f'gs://{output_bucket_prefix}',
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )
        data: Dict[str, Any] = await resp.json()

        return self.datastore_operation_kind.from_repr(data)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects.operations/get
    async def get_datastore_operation(
        self, name: str,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> DatastoreOperation:
        url = f'{self._api_root}/{name}'

        headers = await self.headers()
        headers.update({
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        data: Dict[str, Any] = await resp.json()

        return self.datastore_operation_kind.from_repr(data)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/lookup
    async def lookup(
            self, keys: List[Key], transaction: Optional[str] = None,
            consistency: Consistency = Consistency.STRONG,
            session: Optional[Session] = None, timeout: int = 10,
    ) -> Dict[str, List[Union[EntityResult, Key]]]:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:lookup'

        if transaction:
            options = {'transaction': transaction}
        else:
            options = {'readConsistency': consistency.value}
        payload = json.dumps({
            'keys': [k.to_repr() for k in keys],
            'readOptions': options,
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )

        data: Dict[str, List[Any]] = await resp.json()

        return {
            'found': [
                self.entity_result_kind.from_repr(e)
                for e in data.get('found', [])
            ],
            'missing': [
                self.entity_result_kind.from_repr(e)
                for e in data.get('missing', [])
            ],
            'deferred': [
                self.key_kind.from_repr(k)
                for k in data.get('deferred', [])
            ],
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/reserveIds
    async def reserveIds(
        self, keys: List[Key], database_id: str = '',
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> None:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:reserveIds'

        payload = json.dumps({
            'databaseId': database_id,
            'keys': [k.to_repr() for k in keys],
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        await s.post(url, data=payload, headers=headers, timeout=timeout)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/rollback
    async def rollback(
        self, transaction: str,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> None:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:rollback'

        payload = json.dumps({
            'transaction': transaction,
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        await s.post(url, data=payload, headers=headers, timeout=timeout)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery
    async def runQuery(
        self, query: BaseQuery,
        transaction: Optional[str] = None,
        consistency: Consistency = Consistency.EVENTUAL,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> QueryResultBatch:
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:runQuery'

        if transaction:
            options = {'transaction': transaction}
        else:
            options = {'readConsistency': consistency.value}
        payload = json.dumps({
            'partitionId': {
                'projectId': project,
                'namespaceId': self.namespace,
            },
            query.json_key: query.to_repr(),
            'readOptions': options,
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )

        data: Dict[str, Any] = await resp.json()
        return self.query_result_batch_kind.from_repr(data['batch'])

    async def delete(
        self, key: Key,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return await self.operate(Operation.DELETE, key, session=session)

    async def insert(
        self, key: Key, properties: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return await self.operate(
            Operation.INSERT, key, properties,
            session=session,
        )

    async def update(
        self, key: Key, properties: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return await self.operate(
            Operation.UPDATE, key, properties,
            session=session,
        )

    async def upsert(
        self, key: Key, properties: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return await self.operate(
            Operation.UPSERT, key, properties,
            session=session,
        )

    # TODO: accept Entity rather than key/properties?
    async def operate(
        self, operation: Operation, key: Key,
        properties: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        transaction = await self.beginTransaction(session=session)
        mutation = self.make_mutation(operation, key, properties=properties)
        return await self.commit(
            [mutation], transaction=transaction,
            session=session,
        )

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'Datastore':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
