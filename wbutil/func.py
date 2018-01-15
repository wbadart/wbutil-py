#!/usr/bin/env python

'''
wbutil/func.py

Functional-programming-oriented utilities.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from functools import partial, reduce
from itertools import chain
from typing import Any, Callable, Iterable

__all__ = ['compose',
           'partialright',
           'starcompose',
           'smartcompose',
           ]

_UnaryFunc = Callable[[Any], Any]
_NAryFunc = Callable[[Iterable[Any]], Iterable[Any]]


def compose(*funcs: Iterable[_UnaryFunc]) -> _UnaryFunc:
    '''
    Returns a function which calls the argument functions in order from left
    to right (first to last). Undefined behavior for non-unary functions.

    >>> from functools import partial; from operator import mul
    >>> times2tostr = compse(partial(mul, 2), str)
    >>> times2tostr(10)
    '20'
    '''
    return lambda arg: reduce(lambda acc, f: f(acc), funcs, arg)


def starcompose(*funcs: Iterable[_NAryFunc]) -> _NAryFunc:
    '''
    Returns a function of *args that applies the argument functions in
    order from left to right (first to last). All supplied frunctions must =
    return an iterable and accept *args.

    >>> switch = lambda a, b: (b, a)
    >>> tup2str = lambda a, b: (str(a), str(b))
    >>> switchandstr = starcompose(switch, tup2str)
    >>> switchandstr(1, 2)
    ('2', '1')
    '''
    return lambda *args: reduce(lambda acc, f: f(*acc), funcs, args)


class smartcompose(object):
    '''
    Represents the composition of a list of functions, appied in order from
    left to right. Uses inspection to determine whether to use a regular or
    unpacked application.

    >>>
    TODO: complete example
    '''

    def __init__(self, *funcs):
        self._funcs = funcs

    def __call__(self, *args):
        acc = args
        for f in self._funcs:
            print(f)
            from pdb import set_trace
            set_trace()
            acc = f(acc)


class partialright(partial):
    '''
    Returns a new function with arguments partially applied from right to left.

    >>> data = [1, 2, 3, 4]
    >>> process_data = partialright(map, data)
    >>> stringified = process_data(str)
    >>> stringified
    ['1', '2', '3', '4']
    '''

    def __call__(self, *args, **kwargs):
        '''Call self as a function.'''
        all_args = chain(args, reversed(self.args))
        return self.func(*all_args, **kwargs)
