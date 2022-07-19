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


def test_query_response_to_dict():
    fields = [
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
        {'name': 'PARTITIONTIME', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
    ]
    rows = [
        {'f': [
            {'v': 'ident1'},
            {'v': '1654122422181'},
            {'v': 'true'},
            {'v': [{'v': {'f': [{'v': {'f': [{'v': 'apples'},
                                             {'v': '1.23'}]}},
                                {'v': {'f': [{'v': 'oranges'},
                                             {'v': '2.34'}]}}]}},
                   {'v': {'f': [{'v': {'f': [{'v': 'aardvarks'},
                                             {'v': '9000.1'}]}}]}}]},
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
            {'v': '1.6540416E9'}]},
    ]
    expected = [
        {
            'PARTITIONTIME': datetime.datetime(2022, 6, 1, 0, 0, tzinfo=utc),
            'id': 'ident1',
            'isfakedata': True,
            'nested': [
                {
                    'nestedagain': [
                        {
                            'item': 'apples',
                            'value': 1.23,
                        },
                        {
                            'item': 'oranges',
                            'value': 2.34,
                        },
                    ],
                },
                {
                    'nestedagain': [
                        {
                            'item': 'aardvarks',
                            'value': 9000.1,
                        },
                    ],
                }
            ],
            'record': {
                'item': 'slothtoes',
                'value': 3,
            },
            'repeated': ['foo', 'bar'],
            'unixtime': 1654122422181,
        },
        {
            'PARTITIONTIME': datetime.datetime(2022, 6, 1, 0, 0, tzinfo=utc),
            'id': 'ident2',
            'isfakedata': False,
            'nested': [],
            'record': {
                'item': 'slothtoes',
                'value': 3,
            },
            'repeated': ['foo', 'bar'],
            'unixtime': 1654122422181,
        },
    ]

    resp = {
        'kind': 'bigquery#queryResponse',
        'schema': {'fields': fields},
        'jobReference': {'projectId': 'sample-project',
                         'jobId': 'job_Tlpl-66ca7a8e365a28084c39ffc52d402671',
                         'location': 'US'},
        'rows': rows,
        'totalRows': '2',
        'totalBytesProcessed': '0',
        'jobComplete': True,
        'cacheHit': True,
    }
    parsed = query_response_to_dict(resp)
    print(parsed)
    assert parsed == expected


def test_nested_records():
    fields = [            {
                'name': 'raw',
                'type': 'RECORD',
                'mode': 'REPEATED',
                'fields': [
                    {
                        'name': 'taste',
                        'type': 'RECORD',
                        'mode': 'REPEATED',
                        'fields': [
                            {
                                'name': 'word',
                                'type': 'STRING',
                                'mode': 'NULLABLE'
                            },
                            {
                                'name': 'start',
                                'type': 'FLOAT',
                                'mode': 'NULLABLE'
                            },
                            {
                                'name': 'end',
                                'type': 'FLOAT',
                                'mode': 'NULLABLE'
                            },
                            {
                                'name': 'confidence',
                                'type': 'FLOAT',
                                'mode': 'NULLABLE'
                            }
                        ]
                    }
                ]
            }

    ]
    rows = [
        {
            'f': [
                {
                    'v': [
                        {
                            'v': {
                                'f': [
                                    {
                                        'v': [
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'hello'
                                                        },
                                                        {
                                                            'v': '1.2'
                                                        },
                                                        {
                                                            'v': '2.34'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            'v': {
                                'f': [
                                    {
                                        'v': [
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'hey'
                                                        },
                                                        {
                                                            'v': '4.2'
                                                        },
                                                        {
                                                            'v': '5.22'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            'v': {
                                'f': [
                                    {
                                        'v': [
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': "I'm"
                                                        },
                                                        {
                                                            'v': '7.2'
                                                        },
                                                        {
                                                            'v': '7.86'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'good'
                                                        },
                                                        {
                                                            'v': '7.86'
                                                        },
                                                        {
                                                            'v': '8.31'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': "I'm"
                                                        },
                                                        {
                                                            'v': '8.31'
                                                        },
                                                        {
                                                            'v': '8.46'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'very'
                                                        },
                                                        {
                                                            'v': '8.46'
                                                        },
                                                        {
                                                            'v': '8.76'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'caffeinated'
                                                        },
                                                        {
                                                            'v': '8.79'
                                                        },
                                                        {
                                                            'v': '9.45'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'this'
                                                        },
                                                        {
                                                            'v': '9.45'
                                                        },
                                                        {
                                                            'v': '9.66'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'morning'
                                                        },
                                                        {
                                                            'v': '9.66'
                                                        },
                                                        {
                                                            'v': '10.05'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'how'
                                                        },
                                                        {
                                                            'v': '10.8'
                                                        },
                                                        {
                                                            'v': '10.92'
                                                        },
                                                        {
                                                            'v': '0.973'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'are'
                                                        },
                                                        {
                                                            'v': '10.92'
                                                        },
                                                        {
                                                            'v': '11.04'
                                                        },
                                                        {
                                                            'v': '0.973'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'you'
                                                        },
                                                        {
                                                            'v': '11.04'
                                                        },
                                                        {
                                                            'v': '11.13'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'doing'
                                                        },
                                                        {
                                                            'v': '11.13'
                                                        },
                                                        {
                                                            'v': '11.4'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            'v': {
                                'f': [
                                    {
                                        'v': [
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'uh'
                                                        },
                                                        {
                                                            'v': '13.8'
                                                        },
                                                        {
                                                            'v': '14.19'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'this'
                                                        },
                                                        {
                                                            'v': '14.19'
                                                        },
                                                        {
                                                            'v': '14.49'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'is'
                                                        },
                                                        {
                                                            'v': '14.61'
                                                        },
                                                        {
                                                            'v': '15.06'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'the'
                                                        },
                                                        {
                                                            'v': '15.09'
                                                        },
                                                        {
                                                            'v': '15.21'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'cup'
                                                        },
                                                        {
                                                            'v': '15.21'
                                                        },
                                                        {
                                                            'v': '15.45'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'I'
                                                        },
                                                        {
                                                            'v': '15.45'
                                                        },
                                                        {
                                                            'v': '15.54'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'currently'
                                                        },
                                                        {
                                                            'v': '15.54'
                                                        },
                                                        {
                                                            'v': '15.93'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'have'
                                                        },
                                                        {
                                                            'v': '15.93'
                                                        },
                                                        {
                                                            'v': '16.14'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'is'
                                                        },
                                                        {
                                                            'v': '16.14'
                                                        },
                                                        {
                                                            'v': '16.32'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'my'
                                                        },
                                                        {
                                                            'v': '16.32'
                                                        },
                                                        {
                                                            'v': '16.86'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'third'
                                                        },
                                                        {
                                                            'v': '18.0'
                                                        },
                                                        {
                                                            'v': '18.42'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'I'
                                                        },
                                                        {
                                                            'v': '18.42'
                                                        },
                                                        {
                                                            'v': '18.51'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'think'
                                                        },
                                                        {
                                                            'v': '18.51'
                                                        },
                                                        {
                                                            'v': '18.69'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': "it's"
                                                        },
                                                        {
                                                            'v': '18.69'
                                                        },
                                                        {
                                                            'v': '18.78'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'my'
                                                        },
                                                        {
                                                            'v': '18.78'
                                                        },
                                                        {
                                                            'v': '18.87'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'third'
                                                        },
                                                        {
                                                            'v': '18.87'
                                                        },
                                                        {
                                                            'v': '19.23'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            'v': {
                                'f': [
                                    {
                                        'v': [
                                            {
                                                'v': {
                                                    'f': [
                                                        {
                                                            'v': 'this'
                                                        },
                                                        {
                                                            'v': '27.0'
                                                        },
                                                        {
                                                            'v': '27.625'
                                                        },
                                                        {
                                                            'v': '1.0'
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

    ]
    expected = [{
    'raw': [
        {
            'taste': [
                {
                    'word': 'hello',
                    'start': 1.2,
                    'end': 2.34,
                    'confidence': 1.0
                }
            ]
        },
        {
            'taste': [
                {
                    'word': 'hey',
                    'start': 4.2,
                    'end': 5.22,
                    'confidence': 1.0
                }
            ]
        },
        {
            'taste': [
                {
                    'word': "I'm",
                    'start': 7.2,
                    'end': 7.86,
                    'confidence': 1.0
                },
                {
                    'word': 'good',
                    'start': 7.86,
                    'end': 8.31,
                    'confidence': 1.0
                },
                {
                    'word': "I'm",
                    'start': 8.31,
                    'end': 8.46,
                    'confidence': 1.0
                },
                {
                    'word': 'very',
                    'start': 8.46,
                    'end': 8.76,
                    'confidence': 1.0
                },
                {
                    'word': 'caffeinated',
                    'start': 8.79,
                    'end': 9.45,
                    'confidence': 1.0
                },
                {
                    'word': 'this',
                    'start': 9.45,
                    'end': 9.66,
                    'confidence': 1.0
                },
                {
                    'word': 'morning',
                    'start': 9.66,
                    'end': 10.05,
                    'confidence': 1.0
                },
                {
                    'word': 'how',
                    'start': 10.8,
                    'end': 10.92,
                    'confidence': 0.973
                },
                {
                    'word': 'are',
                    'start': 10.92,
                    'end': 11.04,
                    'confidence': 0.973
                },
                {
                    'word': 'you',
                    'start': 11.04,
                    'end': 11.13,
                    'confidence': 1.0
                },
                {
                    'word': 'doing',
                    'start': 11.13,
                    'end': 11.4,
                    'confidence': 1.0
                }
            ]
        },
        {
            'taste': [
                {
                    'word': 'uh',
                    'start': 13.8,
                    'end': 14.19,
                    'confidence': 1.0
                },
                {
                    'word': 'this',
                    'start': 14.19,
                    'end': 14.49,
                    'confidence': 1.0
                },
                {
                    'word': 'is',
                    'start': 14.61,
                    'end': 15.06,
                    'confidence': 1.0
                },
                {
                    'word': 'the',
                    'start': 15.09,
                    'end': 15.21,
                    'confidence': 1.0
                },
                {
                    'word': 'cup',
                    'start': 15.21,
                    'end': 15.45,
                    'confidence': 1.0
                },
                {
                    'word': 'I',
                    'start': 15.45,
                    'end': 15.54,
                    'confidence': 1.0
                },
                {
                    'word': 'currently',
                    'start': 15.54,
                    'end': 15.93,
                    'confidence': 1.0
                },
                {
                    'word': 'have',
                    'start': 15.93,
                    'end': 16.14,
                    'confidence': 1.0
                },
                {
                    'word': 'is',
                    'start': 16.14,
                    'end': 16.32,
                    'confidence': 1.0
                },
                {
                    'word': 'my',
                    'start': 16.32,
                    'end': 16.86,
                    'confidence': 1.0
                },
                {
                    'word': 'third',
                    'start': 18.0,
                    'end': 18.42,
                    'confidence': 1.0
                },
                {
                    'word': 'I',
                    'start': 18.42,
                    'end': 18.51,
                    'confidence': 1.0
                },
                {
                    'word': 'think',
                    'start': 18.51,
                    'end': 18.69,
                    'confidence': 1.0
                },
                {
                    'word': "it's",
                    'start': 18.69,
                    'end': 18.78,
                    'confidence': 1.0
                },
                {
                    'word': 'my',
                    'start': 18.78,
                    'end': 18.87,
                    'confidence': 1.0
                },
                {
                    'word': 'third',
                    'start': 18.87,
                    'end': 19.23,
                    'confidence': 1.0
                }
            ]
        },
        {
            'taste': [
                {
                    'word': 'this',
                    'start': 27.0,
                    'end': 27.625,
                    'confidence': 1.0
                }
            ]
        }
    ]
}
    ]

    resp = {
        'kind': 'bigquery#queryResponse',
        'schema': {'fields': fields},
        'jobReference': {'projectId': 'sample-project',
                         'jobId': 'job_Tlpl-66ca7a8e365a28084c39ffc52d402671',
                         'location': 'US'},
        'rows': rows,
        'totalRows': '1',
        'totalBytesProcessed': '0',
        'jobComplete': True,
        'cacheHit': True,
    }
    parsed = query_response_to_dict(resp)
    print(parsed)
    assert parsed == expected
