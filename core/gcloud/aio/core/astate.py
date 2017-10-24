import asyncio
import logging

from gcloud.aio.core.aio import fire


log = logging.getLogger(__name__)


class AwaitableState:
    # pylint: disable=too-few-public-methods

    """
    Wrap a :future with a name and data. If :future is a coroutine, turn it
    into a future by firing it.

    Use instances of AwaitableState as named states in state machines. Use
    :data for arbitrary context beyond :name.
    """

    def __init__(self, name, future, data=None):

        self.name = name
        self.future = future
        self.data = data

        if asyncio.iscoroutine(self.future):
            self.future = fire(self.future)

    def __await__(self):

        return self.future.__await__()

    def __str__(self):

        return self.__repr__()

    def __repr__(self):

        return '<awaitable state: {} at 0x{}>'.format(
            self.name,
            id(self)
        )

    def __getattr__(self, attr):

        return getattr(self.future, attr)

    def __hash__(self):

        return hash(self.name)

    def __eq__(self, other):

        return hash(self) == hash(other)


def make_stepper(default_step, state_step, name='sm'):

    """
    `default_step`: a callable that takes no args
    `state_step`: a mapping between AwaitableState.name -> callable
    """

    async def step(state, args):

        state_name = getattr(state, 'name', None)
        step = state_step.get(state_name, default_step)
        next_state = step(args) if args is not None else step()

        if next_state:
            args = await next_state
        else:
            args = tuple()

        if next_state != state:
            log.debug('%s state change: %s -> %s', name,
                      getattr(state, 'name', None),
                      getattr(next_state, 'name', None))

        return next_state, args

    return step
