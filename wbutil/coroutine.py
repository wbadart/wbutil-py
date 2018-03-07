#!/usr/bin/env python3

'''
wbutil/coroutine.py

Helpers for easy coroutine usage.

Will Badart <wbadart@live.com>
created: FEB 2018
'''

import wbutil.misc as m

from asyncio import sleep
from functools import wraps
from pprint import pprint
from time import time
from typing import Any, Callable, Coroutine, Generator

__all__ = [
    'broadcast',
    'prime_coroutine',
]


def prime_coroutine(func: Callable) -> Callable:
    '''
    Takes a generator-based coroutine and starts it immediately after
    construction (so you don't have to remember to prime the coroutine).
    TODO: complete example
    '''
    def _impl(*args, **kwargs):
        routine = func(*args, **kwargs)
        routine.send(None)
        return routine
    return _impl


def iteratee_to_coroutine(func: Callable) -> Callable:
    '''
    '''
    @wraps(func)
    def _impl(target):
        while True:
            target.send(func((yield)))
    return _impl


@prime_coroutine
def broadcast(*targets: Coroutine) -> Generator:
    '''
    Send an item to multiple target coroutines.
    TODO: complete example
    '''
    while True:
        item = (yield)
        for target in targets:
            target.send(item)


@prime_coroutine
def printer():
    '''
    Sink for printing pipeline items.
    TODO: complete example
    '''
    while True:
        item = (yield)
        print(item)


@prime_coroutine
def pprinter():
    '''
    Sink for pretty printing pipeline items.
    TODO: complete example
    '''
    while True:
        item = (yield)
        pprint(item)
        print()


class slow(m.slow):
    '''
    '''

    def __call__(self, func: Callable) -> Any:
        '''
        '''
        @wraps(func)
        def _impl(*args, **kwargs):
            time_elapsed = time() - self.last_call
            if time_elapsed < self.wait:
                yield from sleep(self.wait - time_elapsed)
            self.last_call = time()
            return func(*args, **kwargs)
        return _impl
