import datetime
import logging

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.constants import TypeName
try:
    import ujson as json
except ModuleNotFoundError:
    import json


API_ROOT = 'https://datastore.googleapis.com/v1/projects'
SCOPES = [
    'https://www.googleapis.com/auth/datastore',
    'https://www.googleapis.com/auth/cloud-platform',
]

log = logging.getLogger(__name__)


def infer_type(value):
    # TODO: support more than just scalars
    type_name = {
        bytes: TypeName.BLOB,
        datetime.datetime: TypeName.TIMESTAMP,
        float: TypeName.DOUBLE,
        int: TypeName.INTEGER,
        str: TypeName.STRING,
        type(False): TypeName.BOOLEAN,
        type(None): TypeName.NULL,
    }.get(type(value))

    if not type_name:
        raise Exception(f'type {type(value)} not supported for DS insert')

    return type_name


def format_timestamp(dt):
    # RFC3339 UTC "Zulu" format, accurate to nanoseconds
    return dt.strftime('%Y-%m-%dT%H:%S:%M.%f000Z')


def format_value(type_name, value):
    formatted_value = {
        TypeName.TIMESTAMP: format_timestamp,
    }.get(type_name, lambda v: v)(value)

    return formatted_value


def make_commit_body(transaction, mode=Mode.TRANSACTIONAL, mutations=None):
    if not mutations:
        raise Exception('At least one mutation record is required.')

    return {
        'mode': mode.value,
        'mutations': mutations,
        'transaction': transaction,
    }


def make_mutation_record(operation, kind, name, properties, project):
    props = make_properties(properties)

    mutation = {
        operation.value: {
            'key': {
                'partitionId': {
                    'projectId': project,
                    'namespaceId': '',
                },
                'path': [
                    {
                        'kind': kind,
                        'name': name,
                    },
                ],
            },
            'properties': props,
        }
    }

    return mutation


def make_properties(properties):
    return {k: make_value(v) for k, v in properties.items()}


def make_value(value):
    type_name = infer_type(value)

    return {
        'excludeFromIndexes': False,
        type_name.value: format_value(type_name, value),
    }


class Datastore(object):
    def __init__(self, project, service_file, session=None, token=None):
        self.project = project
        self.session = session
        self.token = token or Token(project, service_file, session=session,
                                    scopes=SCOPES)

    async def headers(self):
        token = await self.token.get()

        return {
            'Authorization': f'Bearer {token}',
        }

    async def transact(self):
        url = f'{API_ROOT}/{self.project}:beginTransaction'
        headers = await self.headers()
        headers.update({
            'Content-Length': '0',
            'Content-Type': 'application/json'
        })

        async with aiohttp.ClientSession() as s:
            response = await s.post(url, data={}, headers=headers, params=None,
                                    timeout=60)
            content = await response.json()

        # TODO: make this raise_for_status-able.
        if 299 >= response.status >= 200:
            transaction = content['transaction']
            return transaction

        log.debug('response code: %d', response.status)
        log.debug('url: %s', url)

        raise Exception(f'could not transact: {content}')

    async def commit(self, transaction, mutations, mode=Mode.TRANSACTIONAL):
        url = f'{API_ROOT}/{self.project}:commit'

        body = make_commit_body(transaction, mode, mutations)
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json'
        })

        async with aiohttp.ClientSession() as s:
            response = await s.post(url, data=payload, headers=headers,
                                    params=None, timeout=60)
            content = await response.json()

        # TODO: make this raise_for_status-able.
        if 299 >= response.status >= 200 and 'insertErrors' not in content:
            return True

        raise Exception(f'{response.status}: {url} > {content}')

    # TODO: look into deletion payload format

    async def insert(self, kind, name, properties, session=None):
        return await self.operate(Operation.INSERT, kind, name, properties,
                                  session=session)

    async def update(self, kind, name, properties, session=None):
        return await self.operate(Operation.UPDATE, kind, name, properties,
                                  session=session)

    async def upsert(self, kind, name, properties, session=None):
        return await self.operate(Operation.UPSERT, kind, name, properties,
                                  session=session)

    async def operate(self, operation, kind, name, properties, session=None):
        # pylint: disable=too-many-arguments
        # TODO: tune pylint argument limits
        transaction = await self.transact()

        session = session or self.session

        mutation = make_mutation_record(operation, kind, name, properties,
                                        self.project)

        return await self.commit(transaction, mutations=[mutation])
