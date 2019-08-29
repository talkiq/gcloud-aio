import gcloud.aio.bigquery as bigquery  # pylint: disable=unused-import


def test_make_insert_body():
    # pylint: disable=protected-access
    body = bigquery.Table._make_insert_body(
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False,
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


def test_make_insert_body_defult_id_fn():
    # pylint: disable=protected-access
    body = bigquery.Table._make_insert_body(
        [{'foo': 'herp', 'bar': 42}, {'foo': 'derp', 'bar': 13}],
        skip_invalid=False, ignore_unknown=False,
        insert_id_fn=bigquery.Table._mk_unique_insert_id)

    assert len(body['rows']) == 2
    assert all(r['insertId'] for r in body['rows'])
