import logging
from typing import Any
from typing import Dict
from typing import List

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.query import GQLQuery
from gcloud.aio.datastore.query import QueryResultBatch
from gcloud.aio.datastore.utils import make_value
try:
    import ujson as json
except ModuleNotFoundError:
    import json  # type: ignore


API_ROOT = 'https://datastore.googleapis.com/v1/projects'
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/datastore',
]

log = logging.getLogger(__name__)


class Datastore:
    def __init__(self, project: str, service_file: str, namespace: str = '',
                 session: aiohttp.ClientSession = None,
                 token: Token = None) -> None:
        self.project = project
        self.namespace = namespace

        self.session = session
        self.token = token or Token(project, service_file, session=session,
                                    scopes=SCOPES)

    @staticmethod
    def _make_commit_body(
            transaction: str, mode: Mode = Mode.TRANSACTIONAL,
            mutations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not mutations:
            raise Exception('at least one mutation record is required')

        return {
            'mode': mode.value,
            'mutations': mutations,
            'transaction': transaction,
        }

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    @staticmethod
    def make_mutation(operation: Operation, key: Key,
                      properties: Dict[str, Any] = None) -> Dict[str, Any]:
        if operation == Operation.DELETE:
            return {operation.value: key.to_repr()}

        return {
            operation.value: {
                'key': key.to_repr(),
                'properties': {k: make_value(v)
                               for k, v in properties.items()},
            }
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/allocateIds
    async def allocateIds(self, keys: List[Key],
                          session: aiohttp.ClientSession = None,
                          timeout: int = 10) -> List[Key]:
        url = f'{API_ROOT}/{self.project}:allocateIds'

        payload = json.dumps({
            'keys': [k.to_repr() for k in keys],
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()
        data = await resp.json()

        return [Key.from_repr(k) for k in data['keys']]

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/beginTransaction
    # TODO: support readwrite vs readonly transaction types
    async def beginTransaction(self, session: aiohttp.ClientSession = None,
                               timeout: int = 10) -> str:
        url = f'{API_ROOT}/{self.project}:beginTransaction'
        headers = await self.headers()
        headers.update({
            'Content-Length': '0',
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = await resp.json()

        transaction: str = data['transaction']
        return transaction

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit
    async def commit(self, transaction: str, mutations: List[Dict[str, Any]],
                     mode: Mode = Mode.TRANSACTIONAL,
                     session: aiohttp.ClientSession = None,
                     timeout: int = 10) -> None:
        url = f'{API_ROOT}/{self.project}:commit'

        body = self._make_commit_body(transaction, mode, mutations)
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/lookup
    async def lookup(self, keys: List[Key], transaction: str = None,
                     consistency: Consistency = Consistency.STRONG,
                     session: aiohttp.ClientSession = None,
                     timeout: int = 10) -> dict:
        url = f'{API_ROOT}/{self.project}:lookup'

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

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()
        data: dict = await resp.json()

        return {
            'found': [EntityResult.from_repr(e)
                      for e in data.get('found', [])],
            'missing': [EntityResult.from_repr(e)
                        for e in data.get('missing', [])],
            'deferred': [Key.from_repr(k) for k in data.get('deferred', [])],
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/reserveIds
    async def reserveIds(self, keys: List[Key], database_id: str = '',
                         session: aiohttp.ClientSession = None,
                         timeout: int = 10) -> None:
        url = f'{API_ROOT}/{self.project}:reserveIds'

        payload = json.dumps({
            'databaseId': database_id,
            'keys': [k.to_repr() for k in keys],
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/rollback
    async def rollback(self, transaction: str,
                       session: aiohttp.ClientSession = None,
                       timeout: int = 10) -> None:
        url = f'{API_ROOT}/{self.project}:rollback'

        payload = json.dumps({
            'transaction': transaction,
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/runQuery
    # TODO: support non-GQL queries
    async def runQuery(self, query: GQLQuery, transaction: str = None,
                       consistency: Consistency = Consistency.EVENTUAL,
                       session: aiohttp.ClientSession = None,
                       timeout: int = 10) -> QueryResultBatch:
        url = f'{API_ROOT}/{self.project}:runQuery'

        if transaction:
            options = {'transaction': transaction}
        else:
            options = {'readConsistency': consistency.value}
        payload = json.dumps({
            'partitionId': {
                'projectId': self.project,
                'namespaceId': self.namespace,
            },
            'gqlQuery': query.to_repr(),
            'readOptions': options,
        }).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        resp = await session.post(url, data=payload, headers=headers,
                                  timeout=timeout)
        resp.raise_for_status()

        data: dict = await resp.json()
        return QueryResultBatch.from_repr(data['batch'])

    async def delete(self, key: Key,
                     session: aiohttp.ClientSession = None) -> None:
        return await self.operate(Operation.DELETE, key, session=session)

    async def insert(self, key: Key, properties: Dict[str, Any],
                     session: aiohttp.ClientSession = None) -> None:
        return await self.operate(Operation.INSERT, key, properties,
                                  session=session)

    async def update(self, key: Key, properties: Dict[str, Any],
                     session: aiohttp.ClientSession = None) -> None:
        return await self.operate(Operation.UPDATE, key, properties,
                                  session=session)

    async def upsert(self, key: Key, properties: Dict[str, Any],
                     session: aiohttp.ClientSession = None) -> None:
        return await self.operate(Operation.UPSERT, key, properties,
                                  session=session)

    async def operate(self, operation: Operation, key: Key,
                      properties: Dict[str, Any] = None,
                      session: aiohttp.ClientSession = None) -> None:
        transaction = await self.beginTransaction(session=session)
        mutation = self.make_mutation(operation, key, properties=properties)
        await self.commit(transaction, mutations=[mutation], session=session)
