#!/usr/bin/env python

'''
wbutil/func.py

Functional-programming-oriented utilities.

Will Badart <wbadart@nd.edu>
created: JAN 2018
'''

from functools import reduce
from typing import Callable, List


def compose(*funcs: List[Callable]) -> Callable:
    '''
    Returns a function which calls the argument functions in order from left to right
    (first to last). Undefined behavior for non-unary functions.

    >>> from functools import partial; from operator import mul
    >>> double2str = compse(partial(mul, 2), str)
    >>> double2str(10)
    '20'
    '''
    return lambda arg: reduce(lambda acc, f: f(acc), funcs, arg)
