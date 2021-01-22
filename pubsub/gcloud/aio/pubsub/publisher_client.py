import io
import json
import logging
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.pubsub.utils import PubsubMessage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]


API_ROOT = 'https://pubsub.googleapis.com/v1'
VERIFY_SSL = True
SCOPES = [
    'https://www.googleapis.com/auth/pubsub',
]


PUBSUB_EMULATOR_HOST = os.environ.get('PUBSUB_EMULATOR_HOST')
if PUBSUB_EMULATOR_HOST:
    API_ROOT = f'http://{PUBSUB_EMULATOR_HOST}/v1'
    VERIFY_SSL = False

log = logging.getLogger(__name__)


class PublisherClient:
    def __init__(self, *, service_file: Optional[Union[str, io.IOBase]] = None,
                 session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self.session = AioSession(session, verify_ssl=VERIFY_SSL)
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session.session)

    @staticmethod
    def project_path(project: str) -> str:
        return f'projects/{project}'

    @classmethod
    def subscription_path(cls, project: str, subscription: str) -> str:
        return f'{cls.project_path(project)}/subscriptions/{subscription}'

    @classmethod
    def topic_path(cls, project: str, topic: str) -> str:
        return f'{cls.project_path(project)}/topics/{topic}'

    async def _headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json'
        }
        if PUBSUB_EMULATOR_HOST:
            return headers

        token = await self.token.get()
        headers['Authorization'] = f'Bearer {token}'
        return headers

    # TODO: implement that various methods from:
    # https://github.com/googleapis/python-pubsub/blob/master/google/cloud/pubsub_v1/gapic/publisher_client.py

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/list
    async def list_topics(self, project: str,
                          query_params: Optional[Dict[str, str]] = None,
                          *, session: Optional[Session] = None,
                          timeout: Optional[int] = 10
                          ) -> Dict[str, Any]:
        """
        List topics
        """
        url = f'{API_ROOT}/{project}/topics'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=query_params,
                           timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/create
    async def create_topic(self, topic: str,
                           body: Optional[Dict[str, Any]] = None,
                           *, session: Optional[Session] = None,
                           timeout: Optional[int] = 10
                           ) -> Dict[str, Any]:
        """
        Create topic.
        """
        url = f'{API_ROOT}/{topic}'
        headers = await self._headers()
        encoded = json.dumps(body or {}).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/delete
    async def delete_topic(self, topic: str,
                           *, session: Optional[Session] = None,
                           timeout: Optional[int] = 10
                           ) -> None:
        """
        Delete topic.
        """
        url = f'{API_ROOT}/{topic}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        await s.delete(url, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/publish
    async def publish(self, topic: str, messages: List[PubsubMessage],
                      session: Optional[Session] = None,
                      timeout: int = 10) -> Dict[str, Any]:
        if not messages:
            return {}

        url = f'{API_ROOT}/{topic}:publish'

        body = {'messages': [m.to_repr() for m in messages]}
        payload = json.dumps(body).encode('utf-8')

        headers = await self._headers()
        headers['Content-Length'] = str(len(payload))

        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=payload, headers=headers,
                            timeout=timeout)
        data: Dict[str, Any] = await resp.json()
        return data

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'PublisherClient':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
