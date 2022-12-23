import json
import uuid
import warnings
from typing import Any
from typing import AnyStr
from typing import Callable
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .bigquery import BigqueryBase
from .bigquery import Disposition
from .bigquery import SchemaUpdateOption
from .bigquery import SourceFormat
from .job import Job

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


class Table(BigqueryBase):
    def __init__(
            self, dataset_name: str, table_name: str,
            project: Optional[str] = None,
            service_file: Optional[Union[str, IO[AnyStr]]] = None,
            session: Optional[Session] = None, token: Optional[Token] = None,
            api_root: Optional[str] = None,
    ) -> None:
        self.dataset_name = dataset_name
        self.table_name = table_name
        super().__init__(
            project=project, service_file=service_file,
            session=session, token=token, api_root=api_root,
        )

    @staticmethod
    def _mk_unique_insert_id(row: Dict[str, Any]) -> str:
        # pylint: disable=unused-argument
        return uuid.uuid4().hex

    def _make_copy_body(
            self, source_project: str, destination_project: str,
            destination_dataset: str,
            destination_table: str,
    ) -> Dict[str, Any]:
        return {
            'configuration': {
                'copy': {
                    'writeDisposition': 'WRITE_TRUNCATE',
                    'destinationTable': {
                        'projectId': destination_project,
                        'datasetId': destination_dataset,
                        'tableId': destination_table,
                    },
                    'sourceTable': {
                        'projectId': source_project,
                        'datasetId': self.dataset_name,
                        'tableId': self.table_name,
                    },
                },
            },
        }

    @staticmethod
    def _make_insert_body(
            rows: List[Dict[str, Any]], *, skip_invalid: bool,
            ignore_unknown: bool, template_suffix: Optional[str],
            insert_id_fn: Callable[[Dict[str, Any]], str]
    ) -> Dict[str, Any]:
        body = {
            'kind': 'bigquery#tableDataInsertAllRequest',
            'skipInvalidRows': skip_invalid,
            'ignoreUnknownValues': ignore_unknown,
            'rows': [
                {
                    'insertId': insert_id_fn(row),
                    'json': row,
                } for row in rows
            ],
        }

        if template_suffix is not None:
            body['templateSuffix'] = template_suffix

        return body

    def _make_load_body(
            self, source_uris: List[str], project: str, autodetect: bool,
            source_format: SourceFormat,
            write_disposition: Disposition,
            ignore_unknown_values: bool,
            schema_update_options: List[SchemaUpdateOption],
    ) -> Dict[str, Any]:
        return {
            'configuration': {
                'load': {
                    'autodetect': autodetect,
                    'ignoreUnknownValues': ignore_unknown_values,
                    'sourceUris': source_uris,
                    'sourceFormat': source_format.value,
                    'writeDisposition': write_disposition.value,
                    'schemaUpdateOptions': [
                        e.value for e in schema_update_options
                    ],
                    'destinationTable': {
                        'projectId': project,
                        'datasetId': self.dataset_name,
                        'tableId': self.table_name,
                    },
                },
            },
        }

    def _make_query_body(
            self, query: str, project: str,
            write_disposition: Disposition,
            use_query_cache: bool,
            dry_run: bool,
    ) -> Dict[str, Any]:
        return {
            'configuration': {
                'query': {
                    'query': query,
                    'writeDisposition': write_disposition.value,
                    'destinationTable': {
                        'projectId': project,
                        'datasetId': self.dataset_name,
                        'tableId': self.table_name,
                    },
                    'useQueryCache': use_query_cache,
                },
                'dryRun': dry_run,
            },
        }

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/insert
    async def create(
        self, table: Dict[str, Any],
        session: Optional[Session] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Create the table specified by tableId from the dataset."""
        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables'
        )

        table['tableReference'] = {
            'projectId': project,
            'datasetId': self.dataset_name,
            'tableId': self.table_name,
        }

        return await self._post_json(url, table, session, timeout)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/patch
    async def patch(
        self, table: Dict[str, Any],
        session: Optional[Session] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Patch an existing table specified by tableId from the dataset."""
        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables/{self.table_name}'
        )

        table['tableReference'] = {
            'projectId': project,
            'datasetId': self.dataset_name,
            'tableId': self.table_name,
        }
        table_data = json.dumps(table).encode('utf-8')

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.patch(
            url, data=table_data, headers=headers,
            timeout=timeout,
        )
        data: Dict[str, Any] = await resp.json()
        return data

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/delete
    async def delete(
        self,
        session: Optional[Session] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Deletes the table specified by tableId from the dataset."""
        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables/{self.table_name}'
        )

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.session.delete(
            url, headers=headers, params=None,
            timeout=timeout,
        )
        try:
            data: Dict[str, Any] = await resp.json()
        except Exception:  # pylint: disable=broad-except
            # For some reason, `gcloud-rest` seems to have intermittent issues
            # parsing this response. In that case, fall back to returning the
            # raw response body.
            try:
                data = {'response': await resp.text()}
            except (AttributeError, TypeError):
                data = {'response': resp.text}

        return data

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables/get
    async def get(
            self, session: Optional[Session] = None,
            timeout: int = 60,
    ) -> Dict[str, Any]:
        """Gets the specified table resource by table ID."""
        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables/{self.table_name}'
        )

        return await self._get_url(url, session, timeout)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tabledata/insertAll
    async def insert(
            self, rows: List[Dict[str, Any]], skip_invalid: bool = False,
            ignore_unknown: bool = True, session: Optional[Session] = None,
            template_suffix: Optional[str] = None,
            timeout: int = 60, *,
            insert_id_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    ) -> Dict[str, Any]:
        """
        Streams data into BigQuery

        By default, each row is assigned a unique insertId. This can be
        customized by supplying an `insert_id_fn` which takes a row and
        returns an insertId.

        In cases where at least one row has successfully been inserted and at
        least one row has failed to be inserted, the Google API will return a
        2xx (successful) response along with an `insertErrors` key in the
        response JSON containing details on the failing rows.
        """
        if not rows:
            return {}

        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables/{self.table_name}/insertAll'
        )

        body = self._make_insert_body(
            rows, skip_invalid=skip_invalid, ignore_unknown=ignore_unknown,
            template_suffix=template_suffix,
            insert_id_fn=insert_id_fn or self._mk_unique_insert_id,
        )
        return await self._post_json(url, body, session, timeout)

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/insert
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/Job#jobconfigurationtablecopy
    async def insert_via_copy(
            self, destination_project: str, destination_dataset: str,
            destination_table: str, session: Optional[Session] = None,
            timeout: int = 60,
    ) -> Job:
        """Copy BQ table to another table in BQ"""
        project = await self.project()
        url = f'{self._api_root}/projects/{project}/jobs'

        body = self._make_copy_body(
            project, destination_project,
            destination_dataset, destination_table,
        )
        response = await self._post_json(url, body, session, timeout)
        return Job(
            response['jobReference']['jobId'], self._project,
            session=self.session.session,  # type: ignore[arg-type]
            token=self.token,
        )

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/insert
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/Job#JobConfigurationLoad
    async def insert_via_load(
            self, source_uris: List[str], session: Optional[Session] = None,
            autodetect: bool = False,
            source_format: SourceFormat = SourceFormat.CSV,
            write_disposition: Disposition = Disposition.WRITE_TRUNCATE,
            timeout: int = 60,
            ignore_unknown_values: bool = False,
            schema_update_options: Optional[List[SchemaUpdateOption]] = None,
    ) -> Job:
        """Loads entities from storage to BigQuery."""
        project = await self.project()
        url = f'{self._api_root}/projects/{project}/jobs'

        body = self._make_load_body(
            source_uris, project, autodetect, source_format, write_disposition,
            ignore_unknown_values, schema_update_options or [],
        )
        response = await self._post_json(url, body, session, timeout)
        return Job(
            response['jobReference']['jobId'], self._project,
            session=self.session.session,  # type: ignore[arg-type]
            token=self.token,
        )

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/insert
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/Job#JobConfigurationQuery
    async def insert_via_query(
            self, query: str, session: Optional[Session] = None,
            write_disposition: Disposition = Disposition.WRITE_EMPTY,
            timeout: int = 60, use_query_cache: bool = True,
            dry_run: bool = False,
    ) -> Job:
        """Create table as a result of the query"""
        warnings.warn(
            'using Table#insert_via_query is deprecated.'
            'use Job#insert_via_query instead', DeprecationWarning,
        )
        project = await self.project()
        url = f'{self._api_root}/projects/{project}/jobs'

        body = self._make_query_body(
            query, project, write_disposition,
            use_query_cache, dry_run,
        )
        response = await self._post_json(url, body, session, timeout)
        job_id = response['jobReference']['jobId'] if not dry_run else None
        return Job(
            job_id, self._project, token=self.token,
            session=self.session.session,  # type: ignore[arg-type]
        )

    # https://cloud.google.com/bigquery/docs/reference/rest/v2/tabledata/list
    async def list_tabledata(
            self, session: Optional[Session] = None, timeout: int = 60,
            params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List the content of a table in rows."""
        project = await self.project()
        url = (
            f'{self._api_root}/projects/{project}/datasets/'
            f'{self.dataset_name}/tables/{self.table_name}/data'
        )

        return await self._get_url(url, session, timeout, params)
