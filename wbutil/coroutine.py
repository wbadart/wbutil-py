#!/usr/bin/env python3

'''
wbutil/coroutine.py

Helpers for easy coroutine usage.

Will Badart <wbadart@live.com>
created: FEB 2018
'''

from typing import Callable, Coroutine, Generator

__all__ = [
    'broadcast',
    'coroutine',
]


def coroutine(func: Callable) -> Callable:
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


@coroutine
def broadcast(*targets: Coroutine) -> Generator:
    '''
    Send an item to multiple target coroutines.
    TODO: complete example
    '''
    while True:
        item = (yield)
        for target in targets:
            target.send(item)
