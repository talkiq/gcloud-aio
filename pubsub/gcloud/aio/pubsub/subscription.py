import asyncio
import logging

import google.auth.exceptions
import google.cloud.pubsub as pubsub
import google.gax.errors
import grpc


log = logging.getLogger(__name__)


class Subscription(pubsub.subscription.Subscription):
    async def acknowledge(self, ack_ids, client=None, retries=0):
        try:
            return super().acknowledge(ack_ids, client=client)
        except (google.auth.exceptions.TransportError,
                google.gax.errors.RetryError):
            # common intermittent communication errors
            if not retries:
                raise

            await asyncio.sleep(1)
        except Exception:
            raise

        return await self.acknowledge(ack_ids, client=client,
                                      retries=retries-1)

    def create_if_missing(self, client=None):
        if self.exists(client=client):
            return

        try:
            self.create(client=client)
        except google.gax.errors.RetryError as e:
            if e.cause._state != grpc.StatusCode.ALREADY_EXISTS:  # pylint: disable=protected-access
                raise

    async def poll(self, max_messages=1, client=None,
                   max_intermittent_errors=1, max_errors=0):
        intermittent_errors = 0
        errors = 0

        while True:
            try:
                for job in self.pull(return_immediately=False,
                                     max_messages=max_messages, client=client):
                    # reset only intermittent errors, not hard errors
                    intermittent_errors = 0

                    yield job
                    await asyncio.sleep(0)
            except (google.auth.exceptions.TransportError,
                    google.gax.errors.RetryError):
                intermittent_errors += 1
                if max_intermittent_errors is not None and \
                        intermittent_errors > max_intermittent_errors:
                    raise

                await asyncio.sleep(1)
            except Exception as e:  # pylint: disable=broad-except
                errors += 1
                if max_errors is not None and errors > max_errors:
                    raise

                log.exception(e)
                await asyncio.sleep(3)
