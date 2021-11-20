import io
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .bigquery import API_ROOT
from .bigquery import BigqueryBase

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]


class Dataset(BigqueryBase):
    def __init__(self, dataset_name: Optional[str] = None,
                 project: Optional[str] = None,
                 service_file: Optional[Union[str, io.IOBase]] = None,
                 session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self.dataset_name = dataset_name
        super().__init__(project=project, service_file=service_file,
                         session=session, token=token)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/list
    async def list_tables(
            self, session: Optional[Session] = None,
            timeout: int = 60,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List tables in a dataset."""
        project = await self.project()
        if not self.dataset_name:
            raise ValueError('could not determine dataset,'
                             ' please set it manually')

        url = (f'{API_ROOT}/projects/{project}/datasets/'
               f'{self.dataset_name}/tables')
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/list
    async def list_datasets(
            self, session: Optional[Session] = None,
            timeout: int = 60,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List datasets in current project."""
        project = await self.project()

        url = (f'{API_ROOT}/projects/{project}/datasets')
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/get
    async def get(self, session: Optional[Session] = None,
                  timeout: int = 60,
                  params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a specific dataset in current project."""
        project = await self.project()
        if not self.dataset_name:
            raise ValueError('could not determine dataset,'
                             ' please set it manually')

        url = (f'{API_ROOT}/projects/{project}/datasets/'
               f'{self.dataset_name}')
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/insert
    async def insert(self, dataset: Dict[str, Any],
                     session: Optional[Session] = None,
                     timeout: int = 60) -> Dict[str, Any]:
        """Create datasets in current project."""
        project = await self.project()

        url = (f'{API_ROOT}/projects/{project}/datasets')
        return await self._post_json(url, dataset, session, timeout)
