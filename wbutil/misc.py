#!/usr/bin/env python

'''
wbutil/misc.py

Miscellaneous utils with no real home elsewhere.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

import signal
from contextlib import ContextDecorator
from functools import wraps
from itertools import count
from time import sleep
from typing import (
    Any, Callable, Generator, Iterable, Optional, Tuple, Type, Union)

__all__ = [
    'uniq',
    'retry',
    'timeout'
]


def uniq(a: Iterable) -> Generator:
    '''
    Generate the argument iterator with the duplicate members removed.

    >>> list(uniq([1, 2, 2, 3]))
    [1, 2, 3]
    '''
    seen: set = set()
    for e in a:
        if e not in seen:
            seen.add(e)
            yield e
        else:
            continue


def retry(
        times: Optional[int]=None,
        wait: int=0,
        exceptions: Union[Type[Exception], Tuple[Type[Exception]]]=Exception,
        default: Any=None) -> Callable:
    '''
    Returns a version of `f' that will automatically retry `times' times if the
    invokation raises any of the given exceptions. Will wait `wait' seconds to
    try again. If `times' is None, will retry indefinitely. Otherwise, when
    retry has reached that many of attempts, it will return `default' or raise
    ValueError if default is None.

    To be used as a decorator, parameters should be given as keyword arguments.

    >>> import requests as r
    >>> fetch = retry(r.get, times=3, exceptions=ConnectionError)
    >>> fetch(URL)
    <Response [200]>
    '''
    def _impl(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            attempts = count() if times is None else range(times)
            first_pass = True
            for _ in attempts:
                if not first_pass:
                    sleep(wait)
                first_pass = False
                try:
                    return f(*args, **kwargs)
                except exceptions:
                    pass
            if default is not None:
                return default
            else:
                raise ValueError(
                    'Function application failed after %d attempts' % times)
        return _wrapper
    return _impl


class timeout(ContextDecorator):
    '''
    Try to execute a block of code, but preempt (raise TimeoutError) if it
    takes too long.

    >>> from time import sleep
    >>> @timeout(1)
    ... def test():
    ...     sleep(5)
    ...     print('Done sleeping')
    ...
    >>> test()
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    TimeoutError: Time allotment of 1 second expired
    >>> with timeout(10):
    ...     sleep(5)
    ...     print('Waited 5 seconds')
    ...
    Waited 5 seconds
    '''

    def __init__(self, duration: int=5) -> None:
        self.duration = duration
        signal.signal(signal.SIGALRM, self._raisetimeout)

    def __enter__(self) -> 'timeout':
        '''Start the block and the timer.'''
        signal.alarm(self.duration)
        return self

    def __exit__(
            self,
            exception_t=Exception,
            exception=None,
            traceback=None) -> None:
        '''Cancel the alarm when block finishes.'''
        signal.alarm(0)

    def _raisetimeout(self, signum: int, frame: Any) -> None:
        '''Trap the alarm signal.'''
        raise TimeoutError(
            'Time allotment of %d second%s expired'
            % (self.duration, 's' if self.duration != 1 else ''))
