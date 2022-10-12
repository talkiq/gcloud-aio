import datetime

import pytest
from gcloud.aio.bigquery.utils import flatten
from gcloud.aio.bigquery.utils import parse
from gcloud.aio.bigquery.utils import query_response_to_dict
from gcloud.aio.bigquery.utils import utc


@pytest.mark.parametrize('data,expected', [
    ({'v': None}, None),
    ({'v': 'foo'}, 'foo'),
    ({'v': [{'v': 0}, {'v': 1}]}, [0, 1]),
    ({'v': {'f': [{'v': 'foo'}]}}, ['foo']),
    ({'v': {'f': [{'v': 'foo'}, {'v': 'bar'}]}}, ['foo', 'bar']),
    ({'v': {'f': [{'v': {'f': [{'v': 0}, {'v': 1}]}},
                  {'v': {'f': [{'v': 2}, {'v': 3}]}}]}}, [[0, 1], [2, 3]]),
])
def test_flatten(data, expected):
    assert flatten({'f': [data]}) == [expected]


@pytest.mark.parametrize('field,value,expected', [
    ({'type': 'BIGNUMERIC', 'mode': 'NULLABLE'}, '0.0', 0.0),
    ({'type': 'BIGNUMERIC', 'mode': 'NULLABLE'}, '1.25', 1.25),

    ({'type': 'BOOLEAN', 'mode': 'NULLABLE'}, 'false', False),
    ({'type': 'BOOLEAN', 'mode': 'NULLABLE'}, 'true', True),

    ({'type': 'FLOAT', 'mode': 'NULLABLE'}, '0.0', 0.0),
    ({'type': 'FLOAT', 'mode': 'NULLABLE'}, '1.25', 1.25),

    ({'type': 'INTEGER', 'mode': 'NULLABLE'}, '0', 0),
    ({'type': 'INTEGER', 'mode': 'NULLABLE'}, '1', 1),

    ({'type': 'NUMERIC', 'mode': 'NULLABLE'}, '0.0', 0.0),
    ({'type': 'NUMERIC', 'mode': 'NULLABLE'}, '1.25', 1.25),

    ({'type': 'RECORD', 'mode': 'NULLABLE', 'fields': [
        {'type': 'INTEGER', 'mode': 'REQUIRED'},
    ]}, [], {}),
    ({'type': 'RECORD', 'mode': 'NULLABLE', 'fields': [
        {'name': 'x', 'type': 'INTEGER', 'mode': 'REQUIRED'},
        {'name': 'y', 'type': 'INTEGER', 'mode': 'REQUIRED'},
    ]}, [1, 2], {'x': 1, 'y': 2}),

    ({'type': 'STRING', 'mode': 'NULLABLE'}, '', ''),
    ({'type': 'STRING', 'mode': 'NULLABLE'}, 'foo', 'foo'),

    ({'type': 'TIMESTAMP', 'mode': 'NULLABLE'}, '0.0',
     datetime.datetime(1970, 1, 1, 0, tzinfo=utc)),
    ({'type': 'TIMESTAMP', 'mode': 'NULLABLE'}, '1656511192.51',
     datetime.datetime(2022, 6, 29, 13, 59, 52, 510000, tzinfo=utc)),

    ({'type': 'STRING', 'mode': 'REQUIRED'}, '', ''),
    ({'type': 'STRING', 'mode': 'REQUIRED'}, 'foo', 'foo'),

    ({'type': 'STRING', 'mode': 'REPEATED'},
     {'v': [{'v': 'foo'}, {'v': 'bar'}]}, ['foo', 'bar']),

])
def test_parse(field, value, expected):
    assert parse(field, value) == expected


@pytest.mark.parametrize('kind', [
    'BOOLEAN',
    'FLOAT',
    'INTEGER',
    'RECORD',
    'STRING',
    'TIMESTAMP',
])
def test_parse_nullable(kind):
    field = {'type': kind, 'mode': 'NULLABLE'}
    # make sure we never convert to a falsey typed equivalent
    # eg. for BOOLEAN, None != False
    assert parse(field, None) is None


@pytest.mark.parametrize('fields,rows,expected', [
    # collection of misc data
    ([
        {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'unixtime', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'isfakedata', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
        {'name': 'nested', 'type': 'RECORD', 'mode': 'REPEATED', 'fields': [
            {'name': 'nestedagain', 'type': 'RECORD', 'mode': 'REPEATED',
             'fields': [
                 {'name': 'item', 'type': 'STRING', 'mode': 'NULLABLE'},
                 {'name': 'value', 'type': 'FLOAT', 'mode': 'NULLABLE'}]}]},
        {'name': 'repeated', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'record', 'type': 'RECORD', 'mode': 'REQUIRED', 'fields': [
            {'name': 'item', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'value', 'type': 'INTEGER', 'mode': 'NULLABLE'}]},
        {'name': 'PARTITIONTIME', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'}],
     [
        {'f': [
            {'v': 'ident1'},
            {'v': '1654122422181'},
            {'v': 'true'},
            {'v': [
                {'v': {'f': [{'v': [
                    {'v': {'f': [{'v': 'apples'}, {'v': '1.23'}]}},
                    {'v': {'f': [{'v': 'oranges'}, {'v': '2.34'}]}}]}]}},
                {'v': {'f': [{'v': [
                    {'v': {'f': [{'v': 'aardvarks'}, {'v': '9000.1'}]}}]}]}}]},
            {'v': [{'v': 'foo'}, {'v': 'bar'}]},
            {'v': {'f': [{'v': 'slothtoes'}, {'v': 3}]}},
            {'v': '1.6540416E9'}]},
        {'f': [
            {'v': 'ident2'},
            {'v': '1654122422181'},
            {'v': 'false'},
            {'v': []},
            {'v': [{'v': 'foo'}, {'v': 'bar'}]},
            {'v': {'f': [{'v': 'slothtoes'}, {'v': 3}]}},
            {'v': '1.6540416E9'}]}],
     [{
         'PARTITIONTIME': datetime.datetime(2022, 6, 1, 0, 0, tzinfo=utc),
         'id': 'ident1',
         'isfakedata': True,
         'nested': [
             {
                 'nestedagain': [
                     {'item': 'apples', 'value': 1.23},
                     {'item': 'oranges', 'value': 2.34},
                 ],
             },
             {
                 'nestedagain': [
                     {'item': 'aardvarks', 'value': 9000.1},
                 ],
             }
         ],
         'record': {'item': 'slothtoes', 'value': 3},
         'repeated': ['foo', 'bar'],
         'unixtime': 1654122422181,
     }, {
         'PARTITIONTIME': datetime.datetime(2022, 6, 1, 0, 0, tzinfo=utc),
         'id': 'ident2',
         'isfakedata': False,
         'nested': [],
         'record': {'item': 'slothtoes', 'value': 3},
         'repeated': ['foo', 'bar'],
         'unixtime': 1654122422181}],
     ),

    # double-nested RECORDs
    ([{
        'name': 'paragraph',
        'type': 'RECORD',
        'mode': 'REPEATED',
        'fields': [
            {
                'name': 'sentence',
                'type': 'RECORD',
                'mode': 'REPEATED',
                'fields': [
                    {
                        'name': 'word',
                        'type': 'STRING',
                        'mode': 'NULLABLE'
                    },
                    {
                        'name': 'timestamp',
                        'type': 'FLOAT',
                        'mode': 'NULLABLE'
                    }]}]}],
     [{'f': [{'v': [
         {'v': {'f': [{'v': [{'v': {'f': [{'v': 'hello'},
                                          {'v': '2.34'}]}}]}]}},
         {'v': {'f': [{'v': [{'v': {'f': [{'v': 'hey'},
                                          {'v': '5.22'}]}}]}]}},
         {'v': {'f': [{'v': [{'v': {'f': [{'v': "I'm"},
                                          {'v': '7.86'}]}},
                             {'v': {'f': [{'v': 'good'},
                                          {'v': '8.31'}]}},
                             {'v': {'f': [{'v': "I'm"},
                                          {'v': '8.46'}]}},
                             {'v': {'f': [{'v': 'very'},
                                          {'v': '8.76'}]}},
                             {'v': {'f': [{'v': 'caffeinated'},
                                          {'v': '9.45'}]}},
                             {'v': {'f': [{'v': 'this'},
                                          {'v': '9.66'}]}},
                             {'v': {'f': [{'v': 'morning'},
                                          {'v': '10.05'}]}},
                             {'v': {'f': [{'v': 'how'},
                                          {'v': '10.92'}]}},
                             {'v': {'f': [{'v': 'are'},
                                          {'v': '11.04'}]}},
                             {'v': {'f': [{'v': 'you'},
                                          {'v': '11.13'}]}},
                             {'v': {'f': [{'v': 'doing'},
                                          {'v': '11.4'}]}}]}]}}]}]}],
     [{'paragraph': [{
         'sentence': [{'word': 'hello', 'timestamp': 2.34}]}, {
         'sentence': [{'word': 'hey', 'timestamp': 5.22}]}, {
         'sentence': [{'word': "I'm", 'timestamp': 7.86},
                      {'word': 'good', 'timestamp': 8.31},
                      {'word': "I'm", 'timestamp': 8.46},
                      {'word': 'very', 'timestamp': 8.76},
                      {'word': 'caffeinated', 'timestamp': 9.45},
                      {'word': 'this', 'timestamp': 9.66},
                      {'word': 'morning', 'timestamp': 10.05},
                      {'word': 'how', 'timestamp': 10.92},
                      {'word': 'are', 'timestamp': 11.04},
                      {'word': 'you', 'timestamp': 11.13},
                      {'word': 'doing', 'timestamp': 11.4}]}]}],
     ),
])
def test_query_response_to_dict(fields, rows, expected):
    resp = {
        'kind': 'bigquery#queryResponse',
        'schema': {'fields': fields},
        'jobReference': {'projectId': 'sample-project',
                         'jobId': 'job_Tlpl-66ca7a8e365a28084c39ffc52d402671',
                         'location': 'US'},
        'rows': rows,
        'totalRows': str(len(rows)),
        'totalBytesProcessed': '0',
        'jobComplete': True,
        'cacheHit': True,
    }
    parsed = query_response_to_dict(resp)
    print(parsed)
    assert parsed == expected
