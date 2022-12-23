import json
import os
from copy import deepcopy
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

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


def init_api_root(api_root: Optional[str]) -> Tuple[bool, str]:
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
            self, *, service_file: Optional[Union[str, IO[AnyStr]]] = None,
            token: Optional[Token] = None, session: Optional[Session] = None,
            api_root: Optional[str] = None,
    ) -> None:
        self._api_is_dev, self._api_root = init_api_root(api_root)

        self.session = AioSession(session, verify_ssl=not self._api_is_dev)
        self.token = token or Token(
            service_file=service_file, scopes=SCOPES,
            session=self.session.session,  # type: ignore[arg-type]
        )

    async def _headers(self) -> Dict[str, str]:
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
        body: Optional[Dict[str, Any]] = None,
        *,
        session: Optional[Session] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Create subscription.
        """
        body = {} if not body else body
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        payload: Dict[str, Any] = deepcopy(body)
        payload.update({'topic': topic})
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/delete
    async def delete_subscription(
        self, subscription: str, *,
        session: Optional[Session] = None,
        timeout: int = 10
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
        *, session: Optional[Session] = None,
        timeout: int = 30
    ) -> List[SubscriberMessage]:
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
        self, subscription: str, ack_ids: List[str],
        *, session: Optional[Session] = None,
        timeout: int = 10
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
        ack_ids: List[str],
        ack_deadline_seconds: int,
        *, session: Optional[Session] = None,
        timeout: int = 10
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
        *, session: Optional[Session] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Get Subscription
        """
        url = f'{self._api_root}/{subscription}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/list
    async def list_subscriptions(
        self, project: str,
        query_params: Optional[Dict[str, str]] = None,
        *, session: Optional[Session] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        List subscriptions
        """
        url = f'{self._api_root}/{project}/subscriptions'
        headers = await self._headers()
        s = AioSession(session) if session else self.session

        all_results: Dict[str, Any] = {'subscriptions': []}
        nextPageToken = None
        next_query_params = query_params if query_params else {}
        while True:
            resp = await s.get(
                url, headers=headers, params=next_query_params,
                timeout=timeout,
            )
            page: Dict[str, Any] = await resp.json()
            all_results['subscriptions'] += page['subscriptions']
            nextPageToken = page.get('nextPageToken', None)
            if not nextPageToken:
                break
            next_query_params.update({'pageToken': nextPageToken})

        return all_results

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'SubscriberClient':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
