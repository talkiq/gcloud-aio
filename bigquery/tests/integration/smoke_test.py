import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.bigquery import Table
from gcloud.aio.datastore import Datastore  # pylint: disable=no-name-in-module
from gcloud.aio.datastore import Key  # pylint: disable=no-name-in-module
from gcloud.aio.datastore import PathElement  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
    from time import sleep
else:
    from aiohttp import ClientSession as Session
    from asyncio import sleep


@pytest.mark.asyncio  # type: ignore
async def test_data_is_inserted(creds: str, dataset: str, project: str,
                                table: str) -> None:
    rows = [{'key': uuid.uuid4().hex, 'value': uuid.uuid4().hex}
            for _ in range(3)]

    async with Session() as s:
        # TODO: create this table (with a random name)
        t = Table(dataset, table, project=project, service_file=creds,
                  session=s)
        await t.insert(rows)


@pytest.mark.asyncio  # type: ignore
async def test_table_load_copy(creds: str, dataset: str, project: str,
                               export_bucket_name: str) -> None:
    # pylint: disable=too-many-locals
    # N.B. this test relies on Datastore.export -- see `test_datastore_export`
    # in the `gcloud-aio-datastore` smoke tests.
    kind = 'PublicTestDatastoreExportModel'

    rand_uuid = str(uuid.uuid4())

    async with Session() as s:
        ds = Datastore(project=project, service_file=creds, session=s)

        await ds.insert(Key(project, [PathElement(kind)]),
                        properties={'rand_str': rand_uuid})

        operation = await ds.export(export_bucket_name, kinds=[kind])

        count = 0
        while (count < 10 and operation and
               operation.metadata['common']['state'] == 'PROCESSING'):
            await sleep(10)
            operation = await ds.get_datastore_operation(operation.name)
            count += 1

        assert operation.metadata['common']['state'] == 'SUCCESSFUL'
        # END: copy from `test_datastore_export`

        uuid_ = str(uuid.uuid4()).replace('-', '_')
        backup_entity_table = f'public_test_backup_entity_{uuid_}'
        copy_entity_table = f'{backup_entity_table}_copy'

        t = Table(dataset, backup_entity_table, project=project,
                  service_file=creds, session=s)
        gs_prefix = operation.metadata['outputUrlPrefix']
        gs_file = (f'{gs_prefix}/all_namespaces/kind_{kind}/'
                   f'all_namespaces_kind_{kind}.export_metadata')
        await t.load([gs_file])

        await sleep(10)

        source_table = await t.get()
        assert int(source_table['numRows']) > 0

        await t.copy(project, dataset, copy_entity_table)
        await sleep(10)
        t1 = Table(dataset, copy_entity_table, project=project,
                   service_file=creds, session=s)
        copy_table = await t1.get()
        assert copy_table['numRows'] == source_table['numRows']

        # delete the backup and copy table
        await t.delete()
        await t1.delete()

        # delete the export file in google storage
        # TODO: confugure the bucket with autodeletion
        prefix_len = len(f'gs://{export_bucket_name}/')
        export_path = operation.metadata['outputUrlPrefix'][prefix_len:]

        storage = Storage(service_file=creds, session=s)
        files = await storage.list_objects(export_bucket_name,
                                           params={'prefix': export_path})
        for file in files['items']:
            await storage.delete(export_bucket_name, file['name'])
