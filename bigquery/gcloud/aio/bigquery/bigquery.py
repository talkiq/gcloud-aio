import datetime
import functools
import logging
import uuid

import aiohttp
from gcloud.aio.auth import Token
try:
    import ujson as json
except ModuleNotFoundError:
    import json


API_ROOT = 'https://www.googleapis.com/bigquery/v2'
INSERT_TEMPLATE = 'projects/{proj}/datasets/{dataset}/tables/{table}/insertAll'
QUERY_TEMPLATE = 'projects/{proj}/queries'
SCOPES = [
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/bigquery.insertdata'
]
QUERY_PARAM_TYPE_MAP = {
    int: 'INT64',
    float: 'NUMERIC',
    str: 'STRING',
    bool: 'BOOL',
    datetime.datetime: 'DATETIME',
}

log = logging.getLogger(__name__)


def make_insert_body(rows, skip_invalid=False, ignore_unknown=True):
    return {
        'kind': 'bigquery#tableDataInsertAllRequest',
        'skipInvalidRows': skip_invalid,
        'ignoreUnknownValues': ignore_unknown,
        'rows': rows
    }


def make_query_body(query, parameters):
    query_parameters = []
    for param_name, param_value in parameters.items:
        param_type = type(param_value)
        try:
            bq_param_type = QUERY_PARAM_TYPE_MAP[param_type]
        except KeyError as ex:
            log.error('Unsupported parameter type %s', param_type, exc_info=ex)
        # TODO do isoformat() for datetime
        query_parameters.append({
            'name': param_name,
            'parameterType': {
                'type': bq_param_type
            },
            'parameterValue': {
                'value': param_value
            }
        })
    query_body = {
        'kind': 'bigquery#queryRequest',
        'query': query,
        'useLegacySql': False
    }
    if query_parameters:
        query_body['parameterMode'] = 'NAMED'
        query_body['queryParameters'] = query_parameters

    return query_parameters


class Table(object):
    def __init__(self, project, service_file, dataset_name, table_name,
                 session=None, token=None):
        # pylint: disable=too-many-arguments
        self.project = project
        self.table_name = table_name
        self.dataset_name = dataset_name

        self.session = session
        self.token = token or Token(project, service_file, session=session,
                                    scopes=SCOPES)

    async def headers(self):
        token = await self.token.get()

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    async def post(self, url, data, params=None, session=None):
        payload = json.dumps(data).encode('utf-8')

        headers = await self.headers()
        headers['Content-Length'] = str(len(data))

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        response = await session.post(url, data=payload, headers=headers,
                                      params=params, timeout=60)
        content = await response.json()
        return response.status, content

    async def insert(self, rows, skip_invalid=False, ignore_unknown=True,
                     session=None):
        insert_url = INSERT_TEMPLATE.format(proj=self.project,
                                            dataset=self.dataset_name,
                                            table=self.table_name)
        url = f'{API_ROOT}/{insert_url}'
        log.info('Inserting %d rows to %s', len(rows), url)

        body = make_insert_body(rows, skip_invalid=skip_invalid,
                                ignore_unknown=ignore_unknown)

        status, content = await self.post(url, body, session=session)

        if 299 >= status >= 200 and 'insertErrors' not in content:
            return True

        log.debug('response code: %d', status)
        log.debug('url: %s', url)
        log.debug('body:\n%s\n', body)

        content_blob = json.dumps(content, sort_keys=True)
        raise Exception(f'could not insert: {content_blob}')

    async def query(self, query, parameters, session=None):
        query_url = QUERY_TEMPLATE.format(proj=self.project)
        url = f'{API_ROOT}/{query_url}'

        body = make_query_body(query, parameters)

        status, content = await self.post(url, body, session=session)

        if 299 >= status >= 200 and 'insertErrors' not in content:
            return True

        content_blob = json.dumps(content, sort_keys=True)
        raise Exception(f'Could not run query: {body} error: {content_blob}')


async def stream_insert(table, rows):
    insert_rows = [{
        'insertId': uuid.uuid4().hex,
        'json': row
    } for row in rows]

    return await table.insert(insert_rows)


def make_stream_insert(project, service_file, dataset_name, table_name,
                       session=None):
    table = Table(
        project,
        service_file,
        dataset_name,
        table_name,
        session=session
    )

    return functools.partial(stream_insert, table)
