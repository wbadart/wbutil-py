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
from numbers import Real
from random import random
from time import sleep, time
from typing import (
    Any, Callable, Generator, Iterable, Optional, Tuple, Type, Union)

__all__ = [
    'pair',
    'randreal',
    'retry',
    'signal_handler',
    'slow',
    'timeout',
    'uniq',
]


def pair(seq: list, e: Any) -> list:
    '''
    For reducing a list to a list of pairs of adjacent elements.

    >>> reduce(pair, range(6), [tuple()])
    [(0, 1), (2, 3), (4, 5)]
    '''
    if len(seq[-1]) == 2:
        seq.append((e,))
    else:
        seq[-1] += (e,)
    return seq


def randreal(min_: Real, max_: Real) -> Real:
    '''
    Generate a pseudo-random number in [min_, max_].

    >>> randreal(10.5, 15.5)
    12.789728304503505
    '''
    return random() * (max_ - min_) + min_


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


def signal_handler(signum: int) -> Callable:
    '''
    Registers a function as the handler of signal `signum'.

    >>> import signal as sig; from os import kill, getpid
    >>> @signal_handler(sig.SIGUSR1)
    ... def f(signum, frame):
    ...     print('Got SIGUSR1')
    ...
    >>> f(None, None)
    Got SIGUSR1
    >>> kill(getpid(), sig.SIGUSR1)
    Got SIGUSR1
    '''
    def _impl(func: Callable[[int, Any], None]) -> Callable[[int, Any], None]:
        signal.signal(signum, func)
        return func
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


class slow(object):
    '''
    Slows the execution of a function. Like a throttle except all calls are
    eventually executed (in sequence).

    >>> from wbutil import timeout
    >>> slow_print = slow(print, 1)
    >>> with timeout(5):
    ...     for i in range(10):
    ...         slow_print(i)
    ...
    0
    1
    2
    3
    4
    Traceback (most recent call last):
      File "<stdin>", line 3, in <module>
      File "wbutil/misc.py", line 150, in __call__
      File "wbutil/misc.py", line 128, in _raisetimeout
    TimeoutError: Time allotment of 5 seconds expired
    '''

    def __init__(self, wait: Union[int, float]) -> None:
        self.wait = wait
        self.last_call = 0.

    def __call__(self, func: Callable) -> Any:
        '''
        '''
        @wraps(func)
        def _impl(*args, **kwargs):
            time_elapsed = time() - self.last_call
            if time_elapsed < self.wait:
                sleep(self.wait - time_elapsed)
            self.last_call = time()
            return func(*args, **kwargs)
        return _impl


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
