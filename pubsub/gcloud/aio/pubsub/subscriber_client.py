import json
import os
from copy import deepcopy
from typing import Any
from typing import AnyStr
from typing import IO

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

from .subscriber_message import SubscriberMessage

if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]

SCOPES = [
    'https://www.googleapis.com/auth/pubsub',
]


def init_api_root(api_root: str | None) -> tuple[bool, str]:
    if api_root:
        return True, api_root

    host = os.environ.get('PUBSUB_EMULATOR_HOST')
    if host:
        return True, f'http://{host}/v1'

    return False, 'https://pubsub.googleapis.com/v1'


class SubscriberClient:
    _api_root: str
    _api_is_dev: bool

    def __init__(
            self, *, service_file: str | IO[AnyStr] | None = None,
            token: Token | None = None, session: Session | None = None,
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

    @classmethod
    def snapshot_path(cls, project: str, snapshot: str) -> str:
        return f'{cls.project_path(project)}/snapshots/{snapshot}'

    async def _headers(self) -> dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
        }
        if self._api_is_dev:
            return headers

        token = await self.token.get()
        headers['Authorization'] = f'Bearer {token}'
        return headers

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/create
    async def create_subscription(
        self,
        subscription: str,
        topic: str,
        body: dict[str, Any] | None = None,
        *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Create subscription.
        """
        body = {} if not body else body
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        payload: dict[str, Any] = deepcopy(body)
        payload.update({'topic': topic})
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/patch
    async def patch_subscription(
        self,
        subscription: str,
        body: dict[str, Any],
        *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        encoded = json.dumps(body).encode()
        s = AioSession(session) if session else self.session
        resp = await s.patch(url, data=encoded, headers=headers,
                             timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/delete
    async def delete_subscription(
        self, subscription: str, *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Delete subscription.
        """
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        await s.delete(url, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull
    async def pull(
        self, subscription: str, max_messages: int,
        *, session: Session | None = None,
        timeout: int = 30,
    ) -> list[SubscriberMessage]:
        """
        Pull messages from subscription
        """
        url = f'{self._api_root}/{subscription}:pull'
        headers = await self._headers()
        payload = {
            'maxMessages': max_messages,
        }
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.post(
            url, data=encoded,
            headers=headers, timeout=timeout,
        )
        data = await resp.json()
        return [
            SubscriberMessage.from_repr(m)
            for m in data.get('receivedMessages', [])
        ]

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/acknowledge
    async def acknowledge(
        self, subscription: str, ack_ids: list[str],
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Acknowledge messages by ackIds
        """
        url = f'{self._api_root}/{subscription}:acknowledge'
        headers = await self._headers()
        payload = {
            'ackIds': ack_ids,
        }
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        await s.post(url, data=encoded, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/modifyAckDeadline
    async def modify_ack_deadline(
        self, subscription: str,
        ack_ids: list[str],
        ack_deadline_seconds: int,
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Modify messages' ack deadline.
        Set ack deadline to 0 to nack messages.
        """
        url = f'{self._api_root}/{subscription}:modifyAckDeadline'
        headers = await self._headers()
        data = json.dumps({
            'ackIds': ack_ids,
            'ackDeadlineSeconds': ack_deadline_seconds,
        }).encode('utf-8')
        s = AioSession(session) if session else self.session
        await s.post(url, data=data, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/get
    async def get_subscription(
        self, subscription: str,
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Get Subscription
        """
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/list
    async def list_subscriptions(
        self, project: str,
        query_params: dict[str, str] | None = None,
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        List subscriptions
        """
        url = f'{self._api_root}/{project}/subscriptions'
        headers = await self._headers()
        s = AioSession(session) if session else self.session

        all_results: dict[str, Any] = {'subscriptions': []}
        next_page_token = None
        next_query_params = query_params if query_params else {}
        while True:
            resp = await s.get(
                url, headers=headers, params=next_query_params,
                timeout=timeout,
            )
            page: dict[str, Any] = await resp.json()
            all_results['subscriptions'] += page['subscriptions']
            next_page_token = page.get('nextPageToken', None)
            if not next_page_token:
                break
            next_query_params.update({'pageToken': next_page_token})

        return all_results

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/seek
    async def seek(
        self, subscription: str,
        body: dict[str, Any],
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Seeks a subscription to a point in time or to a given snapshot.
        """
        url = f'{self._api_root}/{subscription}:seek'
        headers = await self._headers()
        encoded = json.dumps(body).encode()
        s = AioSession(session) if session else self.session
        await s.post(url, data=encoded, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.snapshots/create
    async def create_snapshot(
        self,
        snapshot: str,
        subscription: str,
        body: dict[str, Any] | None = None,
        *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Create snapshot.
        """
        body = {} if not body else body
        url = f'{self._api_root}/{snapshot}'
        headers = await self._headers()
        payload: dict[str, Any] = deepcopy(body)
        payload.update({'subscription': subscription})
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.snapshots/delete
    async def delete_snapshot(
        self, snapshot: str, *,
        session: Session | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Delete snapshot.
        """
        url = f'{self._api_root}/{snapshot}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        await s.delete(url, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.snapshots/list
    async def list_snapshots(
        self, project: str,
        query_params: dict[str, str] | None = None,
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        List snapshots
        """
        url = f'{self._api_root}/{project}/snapshots'
        headers = await self._headers()
        s = AioSession(session) if session else self.session

        all_results: dict[str, Any] = {'snapshots': []}
        nextPageToken = None
        next_query_params = query_params if query_params else {}
        while True:
            resp = await s.get(
                url, headers=headers, params=next_query_params,
                timeout=timeout,
            )
            page: dict[str, Any] = await resp.json()
            all_results['snapshots'] += page['snapshots']
            nextPageToken = page.get('nextPageToken', None)
            if not nextPageToken:
                break
            next_query_params.update({'pageToken': nextPageToken})

        return all_results

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.snapshots/get
    async def get_snapshot(
        self, snapshot: str,
        *, session: Session | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Get snapshot
        """
        url = f'{self._api_root}/{snapshot}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        result: dict[str, Any] = await resp.json()
        return result

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'SubscriberClient':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
