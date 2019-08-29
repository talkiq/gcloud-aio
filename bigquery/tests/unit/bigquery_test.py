import gcloud.aio.bigquery as bigquery  # pylint: disable=unused-import


def test_importable():
    assert True


def test_make_insert_body():
    body = bigquery.Table._make_insert_body(
        [
            {'foo': 'herp', 'bar': 42},
            {'foo': 'derp', 'bar': 13},
        ],
        skip_invalid=False,
        ignore_unknown=False,
        insert_id_fn=lambda b: b['bar']
    )

    assert body == {
            'kind': 'bigquery#tableDataInsertAllRequest',
            'skipInvalidRows': False,
            'ignoreUnknownValues': False,
            'rows': [
                {'insertId': 42, 'json': {'foo': 'herp', 'bar': 42}},
                {'insertId': 13, 'json': {'foo': 'derp', 'bar': 13}},
            ],
        }
