from typing import Any
from typing import AnyStr
from typing import IO

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .bigquery import BigqueryBase

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


class Dataset(BigqueryBase):
    def __init__(
            self, dataset_name: str | None = None,
            project: str | None = None,
            service_file: str | IO[AnyStr] | None = None,
            session: Session | None = None, token: Token | None = None,
            api_root: str | None = None,
    ) -> None:
        self.dataset_name = dataset_name
        super().__init__(
            project=project, service_file=service_file,
            session=session, token=token, api_root=api_root,
        )

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/list
    async def list_tables(
            self, session: Session | None = None,
            timeout: int = 60,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List tables in a dataset."""
        project = await self.project()
        if not self.dataset_name:
            raise ValueError(
                'could not determine dataset,'
                ' please set it manually',
            )

        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables'
        )
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/list
    async def list_datasets(
            self, session: Session | None = None,
            timeout: int = 60,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List datasets in current project."""
        project = await self.project()

        url = f'{self._api_root}/projects/{project}/datasets'
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/get
    async def get(
        self, session: Session | None = None,
        timeout: int = 60,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get a specific dataset in current project."""
        project = await self.project()
        if not self.dataset_name:
            raise ValueError(
                'could not determine dataset,'
                ' please set it manually',
            )

        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}'
        )
        return await self._get_url(url, session, timeout, params=params)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/insert
    async def insert(
        self, dataset: dict[str, Any],
        session: Session | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Create datasets in current project."""
        project = await self.project()

        url = f'{self._api_root}/projects/{project}/datasets'
        return await self._post_json(url, dataset, session, timeout)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets/delete
    async def delete(
        self, dataset_name: str | None = None,
        session: Session | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Delete datasets in current project."""
        project = await self.project()
        dataset_name = dataset_name or self.dataset_name

        url = f'{self._api_root}/projects/{project}/datasets/{dataset_name}'
        return await self._delete(url, session, timeout)
