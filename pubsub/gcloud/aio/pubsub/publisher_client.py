import json
import logging
import os
from typing import Any
from typing import AnyStr
from typing import IO

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .utils import PubsubMessage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


SCOPES = [
    'https://www.googleapis.com/auth/pubsub',
]

log = logging.getLogger(__name__)


def init_api_root(api_root: str | None) -> tuple[bool, str]:
    if api_root:
        return True, api_root

    host = os.environ.get('PUBSUB_EMULATOR_HOST')
    if host:
        return True, f'http://{host}/v1'

    return False, 'https://pubsub.googleapis.com/v1'


class PublisherClient:
    _api_root: str
    _api_is_dev: bool

    # TODO: add project override
    def __init__(
            self, *, service_file: str | IO[AnyStr] | None = None,
            session: Session | None = None, token: Token | None = None,
            api_root: str | None = None,
    ) -> None:
        self._api_is_dev, self._api_root = init_api_root(api_root)

        self.session = AioSession(session, verify_ssl=not self._api_is_dev)
        self.token = token or Token(
            service_file=service_file, scopes=SCOPES,
            session=self.session.session,  # type: ignore[arg-type]
        )

    @staticmethod
    def project_path(project: str) -> str:
        return f'projects/{project}'

    @classmethod
    def subscription_path(cls, project: str, subscription: str) -> str:
        return f'{cls.project_path(project)}/subscriptions/{subscription}'

    @classmethod
    def topic_path(cls, project: str, topic: str) -> str:
        return f'{cls.project_path(project)}/topics/{topic}'

    async def _headers(self) -> dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
        }
        if self._api_is_dev:
            return headers

        token = await self.token.get()
        headers['Authorization'] = f'Bearer {token}'
        return headers

    # TODO: implement that various methods from:
    # https://github.com/googleapis/python-pubsub/blob/master/google/cloud/pubsub_v1/gapic/publisher_client.py

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/list
    async def list_topics(
        self, project: str,
        query_params: dict[str, str] | None = None, *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        List topics
        """
        url = f'{self._api_root}/{project}/topics'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(
            url, headers=headers, params=query_params,
            timeout=timeout,
        )
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/create
    async def create_topic(
        self, topic: str,
        body: dict[str, Any] | None = None, *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Create topic.
        """
        url = f'{self._api_root}/{topic}'
        headers = await self._headers()
        encoded = json.dumps(body or {}).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/delete
    async def delete_topic(
        self, topic: str, *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Delete topic.
        """
        url = f'{self._api_root}/{topic}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        await s.delete(url, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/publish
    async def publish(
        self, topic: str, messages: list[PubsubMessage],
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        if not messages:
            return {}

        url = f'{self._api_root}/{topic}:publish'

        body = {'messages': [m.to_repr() for m in messages]}
        payload = json.dumps(body).encode('utf-8')

        headers = await self._headers()
        headers['Content-Length'] = str(len(payload))

        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=payload, headers=headers,
            timeout=timeout,
        )
        data: dict[str, Any] = await resp.json()
        return data

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'PublisherClient':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
