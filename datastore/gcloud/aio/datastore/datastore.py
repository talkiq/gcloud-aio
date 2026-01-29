import json
import logging
import os
from typing import Any
from typing import AnyStr
from typing import IO

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .constants import Consistency
from .constants import Mode
from .constants import Operation
from .datastore_operation import DatastoreOperation
from .entity import EntityResult
from .key import Key
from .mutation import MutationResult
from .query import BaseQuery
from .query import QueryResult
from .query import QueryResultBatch
from .query_explain import ExplainOptions
from .transaction_options import TransactionOptions
from .value import Value

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

LookUpResult = dict[str, str | list[EntityResult | Key]]


def init_api_root(api_root: str | None) -> tuple[bool, str]:
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
    query_result_kind = QueryResult
    value_kind = Value

    _project: str | None
    _api_root: str
    _api_is_dev: bool

    def __init__(
            self, project: str | None = None,
            service_file: str | IO[AnyStr] | None = None,
            namespace: str = '', session: Session | None = None,
            token: Token | None = None, api_root: str | None = None,
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
        mutations: list[dict[str, Any]],
        transaction: str | None = None,
        mode: Mode = Mode.TRANSACTIONAL,
    ) -> dict[str, Any]:
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

    async def headers(self) -> dict[str, str]:
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
            properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        self, keys: list[Key],
        session: Session | None = None,
        timeout: float = 10.,
    ) -> list[Key]:
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
        self, session: Session | None = None,
        timeout: float = 10.,
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
        self, mutations: list[dict[str, Any]],
        transaction: str | None = None,
        mode: Mode = Mode.TRANSACTIONAL,
        session: Session | None = None,
        timeout: float = 10.,
    ) -> dict[str, Any]:
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
        data: dict[str, Any] = await resp.json()

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
        kinds: list[str] | None = None,
        namespaces: list[str] | None = None,
        labels: dict[str, str] | None = None,
        session: Session | None = None,
        timeout: float = 10.,
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
        data: dict[str, Any] = await resp.json()

        return self.datastore_operation_kind.from_repr(data)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects.operations/get
    async def get_datastore_operation(
        self, name: str,
        session: Session | None = None,
        timeout: float = 10.,
    ) -> DatastoreOperation:
        url = f'{self._api_root}/{name}'

        headers = await self.headers()
        headers.update({
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        data: dict[str, Any] = await resp.json()

        return self.datastore_operation_kind.from_repr(data)

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/lookup
    async def lookup(
            self, keys: list[Key],
            transaction: str | None = None,
            newTransaction: TransactionOptions | None = None,
            consistency: Consistency = Consistency.STRONG,
            read_time: str | None = None,
            session: Session | None = None, timeout: float = 10.,
    ) -> LookUpResult:
        # pylint: disable=too-many-locals
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:lookup'

        read_options = self._build_read_options(
            consistency, newTransaction, transaction, read_time,
        )

        payload = json.dumps({
            'keys': [k.to_repr() for k in keys],
            'readOptions': read_options,
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

        data: dict[str, Any] = await resp.json()

        return self._build_lookup_result(data)

    def _build_lookup_result(self, data: dict[str, Any]) -> LookUpResult:
        result: LookUpResult = {
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
        if 'transaction' in data:
            new_transaction: str = data['transaction']
            result['transaction'] = new_transaction
        if 'readTime' in data:
            read_time: str = data['readTime']
            result['readTime'] = read_time
        return result

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/ReadOptions
    def _build_read_options(
            self, consistency: Consistency,
            newTransaction: TransactionOptions | None,
            transaction: str | None, read_time: str | None,
    ) -> dict[str, Any]:
        # TODO: expose ReadOptions directly to users
        if transaction:
            return {'transaction': transaction}

        if newTransaction:
            return {'newTransaction': newTransaction.to_repr()}

        if read_time:
            return {'readTime': read_time}

        return {'readConsistency': consistency.value}

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/reserveIds
    async def reserveIds(
        self, keys: list[Key], database_id: str = '',
        session: Session | None = None,
        timeout: float = 10.,
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
        session: Session | None = None,
        timeout: float = 10.,
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
        explain_options: ExplainOptions | None = None,
        transaction: str | None = None,
        newTransaction: TransactionOptions | None = None,
        consistency: Consistency = Consistency.EVENTUAL,
        read_time: str | None = None,
        session: Session | None = None,
        timeout: float = 10.,
    ) -> QueryResult:
        # pylint: disable=too-many-locals
        project = await self.project()
        url = f'{self._api_root}/projects/{project}:runQuery'

        read_options = self._build_read_options(
            consistency, newTransaction, transaction, read_time,
        )

        payload_dict = {
            'partitionId': {
                'projectId': project,
                'namespaceId': self.namespace,
            },
            query.json_key: query.to_repr(),
            'readOptions': read_options,
        }
        if explain_options:
            payload_dict['explainOptions'] = explain_options.to_repr()
        payload = json.dumps(payload_dict).encode('utf-8')

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

        data: dict[str, Any] = await resp.json()
        return self.query_result_kind.from_repr(data)

    async def delete(
        self, key: Key,
        session: Session | None = None,
    ) -> dict[str, Any]:
        return await self.operate(Operation.DELETE, key, session=session)

    async def insert(
        self, key: Key, properties: dict[str, Any],
        session: Session | None = None,
    ) -> dict[str, Any]:
        return await self.operate(
            Operation.INSERT, key, properties,
            session=session,
        )

    async def update(
        self, key: Key, properties: dict[str, Any],
        session: Session | None = None,
    ) -> dict[str, Any]:
        return await self.operate(
            Operation.UPDATE, key, properties,
            session=session,
        )

    async def upsert(
        self, key: Key, properties: dict[str, Any],
        session: Session | None = None,
    ) -> dict[str, Any]:
        return await self.operate(
            Operation.UPSERT, key, properties,
            session=session,
        )

    # TODO: accept Entity rather than key/properties?
    async def operate(
        self, operation: Operation, key: Key,
        properties: dict[str, Any] | None = None,
        session: Session | None = None,
    ) -> dict[str, Any]:
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
