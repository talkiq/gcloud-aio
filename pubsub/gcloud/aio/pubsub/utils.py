from typing import Dict
from typing import Union

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import encode  # pylint: disable=no-name-in-module


if BUILD_GCLOUD_REST:
    pass
else:
    import asyncio
    import concurrent
    import threading

    import google.api_core.future


    def convert_google_future_to_concurrent_future(
            future: google.api_core.future.Future, *,
            loop: asyncio.AbstractEventLoop) -> None:
        """
        The google-cloud-pubsub subscription library returns a
        `google.cloud.pubsub_v1.subscriber.futures.StreamingPullFuture`,
        which is a subclass of `google.api_core.future.Future`, which in turn
        is NOT a subclass of `concurrent.futures.Future` (even though it is
        explicitly designed to be interface-identical).

        A `concurrent.futures.Future` can be added to an asyncio task queue
        with `asyncio.wrap_future`, but that method explicitly calls
        `isinstance` rather than duck-typing the future.

        This method exists as a hack to make `asyncio.wrap_future` think that
        a google `Future` is valid.

        Here are the gotchas is uses to do so:
        - sets `future.__class__` so the `isinstance` check works
        - sets `future._condition`, `future._state`, `future._done_callbacks`
          and `future._waiters` to their equivalent expected values (these are
          the attributes which Google decided to avoid mirroring from
          `concurrent.futures`)
        - spawns an infinite task which `await`s every second, which prevents
          the Google future from occasionally getting stuck
        """
        # BEWARE: here be dragons
        async def await_on_interval(interval: int) -> None:
            while True:
                await asyncio.sleep(interval)

        def _state(self: concurrent.futures.Future) -> str:  # type: ignore
            return 'RUNNING' if self.running() else 'FINISHED'

        future._condition = threading.Condition()  # pylint: disable=protected-access
        future.__class__ = concurrent.futures.Future
        setattr(future, '_state', property(_state))
        setattr(future, '_done_callbacks',
                future._callbacks)  # pylint: disable=protected-access
        setattr(future, '_waiters', [])

        loop.create_task(await_on_interval(1))


# https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
class PubsubMessage:
    def __init__(self, data: Union[bytes, str],
                 **kwargs: Dict[str, str]) -> None:
        self.data = data
        self.attributes = kwargs

    def __repr__(self) -> str:
        return str(self.to_repr())

    def to_repr(self) -> Dict[str, str]:
        return {
            'data': encode(self.data).decode('utf-8'),
            'attributes': self.attributes,
        }
