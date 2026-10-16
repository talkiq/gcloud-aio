import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.bigquery import Table

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import HTTPError as ResponseError
else:
    from aiohttp import ClientResponseError as ResponseError


@pytest.mark.asyncio
async def test_delete(api_root):
    async with Table('dataset', 'table', api_root=api_root) as table:
        assert await table.delete() == {'response': ''}


@pytest.mark.asyncio
@pytest.mark.parametrize('insert', [
    lambda table: table.insert_via_copy('project', 'dataset', 'copy'),
    lambda table: table.insert_via_load(['gs://bucket/object.csv']),
    lambda table: table.insert_via_query('SELECT 1'),
])
@pytest.mark.filterwarnings('ignore:using Table#insert_via_query')
async def test_insert_jobs_use_table_api_root(api_root, insert):
    async with Table('dataset', 'table', api_root=api_root) as table:
        job = await insert(table)
        result = await job.get_job()

    print(result)
    assert result == {'jobReference': {'jobId': 'fake-job'}}


@pytest.mark.asyncio
async def test_delete_raises_for_status(api_root):
    async with Table('dataset', 'missing', api_root=api_root) as table:
        with pytest.raises(ResponseError) as excinfo:
            await table.delete()

    error = excinfo.value
    status = error.response.status_code if BUILD_GCLOUD_REST else error.status
    assert status == 404
