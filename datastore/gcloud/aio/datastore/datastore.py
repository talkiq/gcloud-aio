import datetime
import logging

from gcloud.aio.auth import Token
from gcloud.aio.core.http import post
from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.constants import TypeName


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
        raise Exception('Type {} not supported for DS insert. :('.format(
            type(value)
        ))

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
            'Authorization': 'Bearer {}'.format(token),
        }

    async def transact(self):
        url = '{}/{}:beginTransaction'.format(API_ROOT, self.project)
        headers = await self.headers()
        body = {}

        status, content = await post(url, payload={}, headers=headers)

        # TODO: make this raise_for_status-able.
        success = 299 >= status >= 200

        if success:
            transaction = content['transaction']
            return transaction

        log.debug('response code: %d', status)
        log.debug('url: %s', url)
        log.debug('body:\n%s\n', body)

        raise Exception('Could not transact: {}'.format(content))

    async def commit(self, transaction, mutations, mode=Mode.TRANSACTIONAL):
        url = '{}/{}:commit'.format(API_ROOT, self.project)

        body = make_commit_body(transaction, mode, mutations)

        headers = await self.headers()

        status, content = await post(url, payload=body, headers=headers)

        # TODO: make this raise_for_status-able.
        success = 299 >= status >= 200 and 'insertErrors' not in content

        if success:
            return success

        raise Exception('{}: {} > {}'.format(status, url, content))

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
