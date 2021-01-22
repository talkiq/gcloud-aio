import json
import os
from copy import deepcopy
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token

from .subscriber_message import SubscriberMessage

if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]

API_ROOT = 'https://pubsub.googleapis.com'
VERIFY_SSL = True

SCOPES = [
    'https://www.googleapis.com/auth/pubsub'
]

PUBSUB_EMULATOR_HOST = os.environ.get('PUBSUB_EMULATOR_HOST')
if PUBSUB_EMULATOR_HOST:
    API_ROOT = f'http://{PUBSUB_EMULATOR_HOST}'
    VERIFY_SSL = False


class SubscriberClient:
    def __init__(self, *,
                 service_file: Optional[Union[str, IO[AnyStr]]] = None,
                 token: Optional[Token] = None,
                 session: Optional[Session] = None) -> None:
        self.session = AioSession(session, verify_ssl=VERIFY_SSL)
        self.token = token or Token(service_file=service_file,
                                    scopes=SCOPES,
                                    session=self.session.session)

    async def _headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json'
        }
        if PUBSUB_EMULATOR_HOST:
            return headers

        token = await self.token.get()
        headers['Authorization'] = f'Bearer {token}'
        return headers

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/create
    async def create_subscription(self,
                                  subscription: str,
                                  topic: str,
                                  body: Optional[Dict[str, Any]] = None,
                                  *,
                                  session: Optional[Session] = None,
                                  timeout: Optional[int] = 10
                                  ) -> Dict[str, Any]:
        """
        Create subscription.
        """
        body = {} if not body else body
        url = f'{API_ROOT}/v1/{subscription}'
        headers = await self._headers()
        payload: Dict[str, Any] = deepcopy(body)
        payload.update({'topic': topic})
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.put(url, data=encoded, headers=headers, timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/delete
    async def delete_subscription(self,
                                  subscription: str,
                                  *,
                                  session: Optional[Session] = None,
                                  timeout: Optional[int] = 10
                                  ) -> None:
        """
        Delete subscription.
        """
        url = f'{API_ROOT}/v1/{subscription}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        await s.delete(url, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull
    async def pull(self, subscription: str, max_messages: int,
                   *, session: Optional[Session] = None,
                   timeout: Optional[int] = 30
                   ) -> List[SubscriberMessage]:
        """
        Pull messages from subscription
        """
        url = f'{API_ROOT}/v1/{subscription}:pull'
        headers = await self._headers()
        payload = {
            'maxMessages': max_messages,
        }
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=encoded, headers=headers,
                            timeout=timeout)
        resp = await resp.json()
        return [
            SubscriberMessage.from_repr(m)
            for m in resp['receivedMessages']
        ]

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/acknowledge
    async def acknowledge(self, subscription: str, ack_ids: List[str],
                          *, session: Optional[Session] = None,
                          timeout: Optional[int] = 10) -> None:
        """
        Acknowledge messages by ackIds
        """
        url = f'{API_ROOT}/v1/{subscription}:acknowledge'
        headers = await self._headers()
        payload = {
            'ackIds': ack_ids,
        }
        encoded = json.dumps(payload).encode()
        s = AioSession(session) if session else self.session
        await s.post(url, data=encoded, headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/modifyAckDeadline
    async def modify_ack_deadline(self, subscription: str,
                                  ack_ids: List[str],
                                  ack_deadline_seconds: int,
                                  *, session: Optional[Session] = None,
                                  timeout: Optional[int] = 10
                                  ) -> None:
        """
        Modify messages' ack deadline.
        Set ack deadline to 0 to nack messages.
        """
        url = f'{API_ROOT}/v1/{subscription}:modifyAckDeadline'
        headers = await self._headers()
        payload = {
            'ackIds': ack_ids,
            'ackDeadlineSeconds': ack_deadline_seconds,
        }
        s = AioSession(session) if session else self.session
        await s.post(url, data=json.dumps(payload).encode('utf-8'),
                     headers=headers, timeout=timeout)

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/get
    async def get_subscription(self, subscription: str,
                               *, session: Optional[Session] = None,
                               timeout: Optional[int] = 10
                               ) -> Dict[str, Any]:
        """
        Get Subscription
        """
        url = f'{API_ROOT}/v1/{subscription}'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result

    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/list
    async def list_subscriptions(self, project: str,
                                 query_params: Optional[Dict[str, str]] = None,
                                 *, session: Optional[Session] = None,
                                 timeout: Optional[int] = 10
                                 ) -> Dict[str, Any]:
        """
        List subscriptions
        """
        url = f'{API_ROOT}/v1/{project}/subscriptions'
        headers = await self._headers()
        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=query_params,
                           timeout=timeout)
        result: Dict[str, Any] = await resp.json()
        return result
