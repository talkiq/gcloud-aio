import logging
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.datastore.constants import Consistency
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.entity import EntityResult
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.query import BaseQuery
from gcloud.aio.datastore.query import QueryResultBatch
from gcloud.aio.datastore.value import Value
try:
    import ujson as json
except ModuleNotFoundError:
    import json  # type: ignore


try:
    API_ROOT = f'http://{os.environ["DATASTORE_EMULATOR_HOST"]}/v1/projects'
    IS_DEV = True
except KeyError:
    API_ROOT = 'https://datastore.googleapis.com/v1/projects'
    IS_DEV = False

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/datastore',
]

log = logging.getLogger(__name__)


class Datastore:
    entity_result_kind = EntityResult
    key_kind = Key
    query_result_batch_kind = QueryResultBatch
    value_kind = Value

    def __init__(self, project: Optional[str] = None,
                 service_file: Optional[str] = None, namespace: str = '',
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        self.namespace = namespace
        self.session = session

        if IS_DEV:
            self._project = os.environ.get('DATASTORE_PROJECT_ID', 'dev')
            # Tokens are not needed when using dev emulator
            self.token = None
        else:
            self._project = project
            self.token = token or Token(service_file=service_file,
                                        session=session, scopes=SCOPES)

    async def project(self) -> str:
        if self._project:
            return self._project

        self._project = await self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    @staticmethod
    def _make_commit_body(mutations: List[Dict[str, Any]],
                          transaction: Optional[str] = None,
                          mode: Mode = Mode.TRANSACTIONAL) -> Dict[str, Any]:
        if not mutations:
            raise Exception('at least one mutation record is required')

        if transaction is None and mode != Mode.NON_TRANSACTIONAL:
            raise Exception('a transaction ID must be provided when mode is '
                            'transactional')

        data = {
            'mode': mode.value,
            'mutations': mutations,
        }
        if transaction is not None:
            data['transaction'] = transaction
        return data

    async def headers(self) -> Dict[str, str]:
        if IS_DEV:
            return {}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    # TODO: support mutations w version specifiers, return new version (commit)
    @classmethod
    def make_mutation(cls, operation: Operation, key: Key,
                      properties: Dict[str, Any] = None) -> Dict[str, Any]:
        if operation == Operation.DELETE:
            return {operation.value: key.to_repr()}

        return {
            operation.value: {
                'key': key.to_repr(),
                'properties': {k: cls.value_kind(v).to_repr()
                               for k, v in properties.items()},
            }
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/allocateIds
    async def allocateIds(self, keys: List[Key],
                          session: aiohttp.ClientSession = None,
                          timeout: int = 10) -> List[Key]:
        project = await self.project()
        url = f'{API_ROOT}/{project}:allocateIds'

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

        return [self.key_kind.from_repr(k) for k in data['keys']]

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/beginTransaction
    # TODO: support readwrite vs readonly transaction types
    async def beginTransaction(self, session: aiohttp.ClientSession = None,
                               timeout: int = 10) -> str:
        project = await self.project()
        url = f'{API_ROOT}/{project}:beginTransaction'
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

    # TODO: return mutation results
    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/commit
    async def commit(self, mutations: List[Dict[str, Any]],
                     transaction: Optional[str] = None,
                     mode: Mode = Mode.TRANSACTIONAL,
                     session: aiohttp.ClientSession = None,
                     timeout: int = 10) -> None:
        project = await self.project()
        url = f'{API_ROOT}/{project}:commit'

        body = self._make_commit_body(mutations, transaction=transaction,
                                      mode=mode)
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
                     timeout: int = 10) -> Dict[str, Union[EntityResult, Key]]:
        project = await self.project()
        url = f'{API_ROOT}/{project}:lookup'

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
            'found': [self.entity_result_kind.from_repr(e)
                      for e in data.get('found', [])],
            'missing': [self.entity_result_kind.from_repr(e)
                        for e in data.get('missing', [])],
            'deferred': [self.key_kind.from_repr(k)
                         for k in data.get('deferred', [])],
        }

    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/projects/reserveIds
    async def reserveIds(self, keys: List[Key], database_id: str = '',
                         session: aiohttp.ClientSession = None,
                         timeout: int = 10) -> None:
        project = await self.project()
        url = f'{API_ROOT}/{project}:reserveIds'

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
        project = await self.project()
        url = f'{API_ROOT}/{project}:rollback'

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
    async def runQuery(self, query: BaseQuery, transaction: str = None,
                       consistency: Consistency = Consistency.EVENTUAL,
                       session: aiohttp.ClientSession = None,
                       timeout: int = 10) -> QueryResultBatch:
        project = await self.project()
        url = f'{API_ROOT}/{project}:runQuery'

        if transaction:
            options = {'transaction': transaction}
        else:
            options = {'readConsistency': consistency.value}
        payload = json.dumps({
            'partitionId': {
                'projectId': project,
                'namespaceId': self.namespace,
            },
            query.json_key:  query.to_repr(),
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
        return self.query_result_batch_kind.from_repr(data['batch'])

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

    # TODO: accept Entity rather than key/properties?
    async def operate(self, operation: Operation, key: Key,
                      properties: Dict[str, Any] = None,
                      session: aiohttp.ClientSession = None) -> None:
        transaction = await self.beginTransaction(session=session)
        mutation = self.make_mutation(operation, key, properties=properties)
        await self.commit([mutation], transaction=transaction, session=session)
