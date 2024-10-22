from typing import Optional

import pytest
from gcloud.aio.bigquery import Table
from gcloud.aio.bigquery.bigquery import BigqueryBase


def test_make_insert_body():
    body = Table._make_insert_body(  # pylint: disable=protected-access
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False, template_suffix=None,
        insert_id_fn=lambda b: b['bar'],
    )

    expected = {
        'kind': 'bigquery#tableDataInsertAllRequest',
        'skipInvalidRows': False,
        'ignoreUnknownValues': False,
        'rows': [
            {'insertId': 42, 'json': {'foo': 'herp', 'bar': 42}},
            {'insertId': 13, 'json': {'foo': 'derp', 'bar': 13}},
        ],
    }

    assert body == expected


def test_make_insert_body_template_suffix():
    body = Table._make_insert_body(  # pylint: disable=protected-access
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False, template_suffix='suffix',
        insert_id_fn=lambda b: b['bar'],
    )

    expected = {
        'kind': 'bigquery#tableDataInsertAllRequest',
        'skipInvalidRows': False,
        'ignoreUnknownValues': False,
        'templateSuffix': 'suffix',
        'rows': [
            {'insertId': 42, 'json': {'foo': 'herp', 'bar': 42}},
            {'insertId': 13, 'json': {'foo': 'derp', 'bar': 13}},
        ],
    }

    assert body == expected


def test_make_insert_body_defult_id_fn():
    insert_id = Table._mk_unique_insert_id  # pylint: disable=protected-access
    body = Table._make_insert_body(  # pylint: disable=protected-access
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False, template_suffix=None,
        insert_id_fn=insert_id,
    )

    assert len(body['rows']) == 2
    assert all(r['insertId'] for r in body['rows'])


# =========
# client
# =========

class _MockToken:
    @staticmethod
    async def get() -> Optional[str]:
        return 'Unit-Test-Bearer-Token'


@pytest.mark.asyncio
async def test_client_api_is_dev():
    """
    Test that the api_is_dev constructor parameter controls whether the
    Authorization header is set on requests
    """
    api_root = 'https://foobar/v1'

    # With no API root specified, assume API not dev, so auth header should be
    # set
    async with BigqueryBase(token=_MockToken()) as bigquery:
        assert 'Authorization' in await bigquery.headers()
    # If API root set and not otherwise specified, assume API is dev, so auth
    # header should not be set
    async with BigqueryBase(api_root=api_root, token=_MockToken()) as bigquery:
        assert 'Authorization' not in await bigquery.headers()
    # If API specified to be dev, auth header should not be set
    async with BigqueryBase(
            api_root=api_root, api_is_dev=True, token=_MockToken(),
    ) as bigquery:
        assert 'Authorization' not in await bigquery.headers()
    # If API specified to not be dev, auth header should be set
    async with BigqueryBase(
            api_root=api_root, api_is_dev=False, token=_MockToken(),
    ) as bigquery:
        assert 'Authorization' in await bigquery.headers()
