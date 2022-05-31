from gcloud.aio.bigquery import Table


def test_make_insert_body():
    body = Table._make_insert_body(  # pylint: disable=protected-access
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False, template_suffix=None,
        insert_id_fn=lambda b: b['bar'])

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
        insert_id_fn=lambda b: b['bar'])

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
        insert_id_fn=insert_id)

    assert len(body['rows']) == 2
    assert all(r['insertId'] for r in body['rows'])
