import asyncio
import functools


def maybe_async(callable_, *args, **kwargs):

    """
    Turn a callable into a coroutine if it isn't
    """

    if asyncio.iscoroutine(callable_):
        return callable_

    return asyncio.coroutine(callable_)(*args, **kwargs)


def fire(callable_, *args, **kwargs):

    """
    Start a callable as a coroutine, and return it's future. The cool thing
    about this function is that (via maybe_async) it lets you treat synchronous
    and asynchronous callables the same (both as async), which simplifies code.
    """

    return asyncio.ensure_future(maybe_async(callable_, *args, **kwargs))


def auto(fn):

    """
    Decorate a function or method with this, and it will become a callable
    that can be scheduled in the event loop just by calling it. Normally you'd
    have to do an `asyncio.ensure_future(my_callable())`. Not you can just do
    `my_callable()`. Twisted has always let you do this, and now you can let
    asyncio do it as well (with a decorator, albeit...)
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):

        return fire(fn, *args, **kwargs)

    return wrapper


async def _call_later(delay, callable_, *args, **kwargs):

    """
    The bus stop, where we wait.
    """

    await asyncio.sleep(delay)

    fire(callable_, *args, **kwargs)


def call_later(delay, callable_, *args, **kwargs):

    """
    After :delay seconds, call :callable with :args and :kwargs; :callable can
    be a synchronous or asynchronous callable (a coroutine). Note that _this_
    function is synchronous - mission accomplished - it can be used from within
    any synchronous or asynchronous callable.
    """

    return fire(_call_later, delay, callable_, *args, **kwargs)
