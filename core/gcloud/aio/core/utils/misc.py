import random
import time
import traceback


def sleep_retry(fn, args=None, kwargs=None, tries=2, sleep_duration=1.0):

    args = args or tuple()
    kwargs = kwargs or {}

    attempts = 0

    while attempts < tries:

        try:

            return fn(*args, **kwargs)

        except Exception:  # pylint: disable=broad-except

            attempts += 1

            print('After {} try(ies) could not create service: {}'.format(
                attempts, traceback.format_exc() or '?'
            ))

            time.sleep(sleep_duration)

    return False


def backoff(base=2, factor=1, max_value=None):

    """Generator for exponential decay.

    The Google docs warn to back off from polling their API if there is no
    work available in a task queue. So we does.

    # modified from:
    # https://github.com/litl/backoff/blob/master/backoff.py

        base: the mathematical base of the exponentiation operation
        factor: factor to multiply the exponentation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """

    n = 0

    # initial backoff delay is nothing
    yield 0

    while True:

        a = factor * base ** n

        if max_value is None or a < max_value:
            yield a
            n += 1
        else:
            yield max_value - random.random() * max_value / 10


SECRETS = []


def secret(o):

    SECRETS.append(o)
    return o


class Config(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument

        self.__dict__.update(**kwargs)

    def __str__(self):

        lines = self.show(depth=0)

        return '\n'.join(lines)

    def show(self, depth=0):

        lines = []

        for k in sorted(self.__dict__):

            v = self.__dict__[k]

            if isinstance(v, self.__class__):
                lines.append('{}{}'.format(
                    '  ' * depth,
                    k
                ))
                lines.extend(v.show(depth=depth + 1))
                continue

            lines.append('{}{}: {}'.format(
                '  ' * depth,
                k,
                '<SECRET>' if v in SECRETS else v
            ))

        return lines
