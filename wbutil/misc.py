#!/usr/bin/env python

'''
wbutil/misc.py

Miscellaneous utils with no real home elsewhere.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from functools import wraps
from itertools import count
from time import sleep
from typing import (
    Any, Callable, Generator, Iterable, Optional, Tuple, Type, Union)

__all__ = [
    'uniq',
    'retry',
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
                raise ValueError('Function application failed')
        return _wrapper
    return _impl
