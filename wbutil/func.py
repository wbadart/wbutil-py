#!/usr/bin/env python

'''
wbutil/func.py

Functional-programming-oriented utilities.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

import re
from functools import partial, reduce, wraps
from inspect import signature
from itertools import chain
from typing import Any, Callable, Generic, Iterable, TypeVar, Union

__all__ = [
    'autocurry',
    'compose',
    'partialright',
    'starcompose',
    'cmap',
    'cfilter',
    'creduce',
    'lmap',
    'lfilter',
    'identity',
    'pred_negate',
]

_ComposeRetT = TypeVar('_ComposeRetT')
_CurryReturnT = TypeVar('_CurryReturnT')
_NAryFunc = Callable[[Iterable[Any]], Iterable[Any]]
_UnaryFunc = Callable[[Any], Any]
_T = TypeVar('_T')


class autocurry(Generic[_CurryReturnT]):
    '''
    Wraps a callable which it autocurries. Calling the function with fewer than
    the total number of parameters yields a partial application, and fulfilling
    the parameter list yields a complete application. Avoid complications by
    not applying this to functions of variable parameters.

    >>> from operator import add
    >>> a = autocurry(add)
    >>> a(3)(4)
    7
    '''

    def __init__(
            self,
            func: Callable[..., _CurryReturnT],
            *args,
            **kwargs) -> None:
        self.func = func
        try:
            self.nparams = len(signature(func).parameters)
        except ValueError:
            func = getattr(func, 'func', func)  # if func is a partial
            prototype = re.search('^[\w_]+(\(.*\))', func.__doc__).groups()[0]
            prototype = prototype[1:-1]
            self.nparams = len(prototype.split(','))

        self.args = args
        self.keywords = kwargs

    def __call__(self, *args, **kwargs) -> Union['autocurry', _CurryReturnT]:
        '''
        Partially apply args and kwargs to the wrapped function (full
        application if all parameters have been filled.
        '''
        pos_args = chain(self.args, args)
        keywords = dict(**self.keywords, **kwargs)
        if len(self.args + args) == self.nparams:
            return self.func(*pos_args, **keywords)
        else:
            return type(self)(self.func, *pos_args, **keywords)


class compose(Generic[_ComposeRetT]):
    '''
    Returns a function which calls the argument functions in order from left
    to right (first to last). Undefined behavior for non-unary functions.

    >>> from functools import partial; from operator import mul
    >>> times2tostr = compse(partial(mul, 2), str)
    >>> times2tostr(10)
    '20'
    '''

    def __init__(self, *funcs: _UnaryFunc) -> None:
        self.funcs = funcs

    def __call__(self, arg: Any) -> _ComposeRetT:
        '''Invoke the composed pipeline with the specified argument.'''
        return reduce(lambda acc, f: f(acc), self.funcs, arg)

    def __reversed__(self) -> 'compose':
        '''
        Gives a composition with the calling order reversed. Allows compose to
        emulate traditional compositional ordering.
        '''
        funcs = tuple(reversed(self.funcs))
        return type(self)(*funcs)


class starcompose(compose):
    '''
    Returns a function of *args that applies the argument functions in
    order from left to right (first to last). All supplied functions must
    return an iterable and accept *args.

    >>> switch = lambda a, b: (b, a)
    >>> tup2str = lambda a, b: (str(a), str(b))
    >>> switchandstr = starcompose(switch, tup2str)
    >>> switchandstr(1, 2)
    ('2', '1')
    '''

    # Overridden to annotate n-ary function support
    def __init__(self, *funcs: _NAryFunc) -> None:
        super().__init__(*funcs)

    def __call__(self, *args: Any) -> Any:
        '''Invoke the composed pipeline with unpacking.'''
        return reduce(lambda acc, f: f(*acc), self.funcs, args)


class partialright(partial):
    '''
    Returns a new function with arguments partially applied from right to left.

    >>> data = [1, 2, 3, 4]
    >>> process_data = partialright(map, data)
    >>> stringified = process_data(str)
    >>> stringified
    ['1', '2', '3', '4']
    '''

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        '''Call self as a function.'''
        pos_args = chain(args, reversed(self.args))
        keywords = self.keywords.copy()
        keywords.update(kwargs)
        return self.func(*pos_args, **keywords)


def cmap(iteratee: Callable[[Any], Any]) -> partial:
    '''
    Curried map. Sugar for partial(map, iteratee).

    >>> from string import digits
    >>> transform = cmap(int)
    >>> list(transform(digits))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    '''
    return partial(map, iteratee)


def cfilter(predicate: Callable[[Any], bool]) -> partial:
    '''
    Curried filter. Sugar for partial(filter, predicate).

    >>> is1or2 = cfilter({1, 2}.__contains__)
    >>> list(is1or2(range(10)))
    [1, 2]
    '''
    return partial(filter, predicate)


def creduce(iteratee: Callable[[Any], Any]) -> partial:
    '''
    Curried reduce. Allows sequence to be supplied later.

    >>> from operator import add
    >>> mysum = creduce(add)
    >>> mysum(range(10)) == sum(range(10))
    True
    >>> from collections import defaultdict
    >>> def byfirst(obj, e):
    ...     obj[e[0]].append(e)
    ...     return obj
    ...
    >>> groupbyfirst = creduce(byfirst)
    >>> groupbyfirst(db.getNames(), defaultdict(list))
    defaultdict(<class 'list'>, {'A': ['Alice', 'Adam'], 'B': ['Bob']})
    '''
    return partial(reduce, iteratee)


def lmap(iteratee: Callable[[Any], Any], iterable: Iterable) -> list:
    '''
    Performs a mapping of `iteratee' over `iterable' and immediately
    serializes result into a list.

    >>> lmap(str, range(10))
    ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    '''
    return list(map(iteratee, iterable))


def lfilter(predicate: Callable[[Any], bool], iterable: Iterable) -> list:
    '''
    Filters `iterable' on `predicate', immediately serializing results into a
    list.

    >>> odd = lambda x: x % 2 == 1
    >>> lfilter(odd, range(10))
    [1, 3, 5, 7, 9]
    '''
    return list(filter(predicate, iterable))


def identity(e: _T) -> _T:
    '''
    Returns the argument untouched. Useful default iteratee.

    >>> list(map(identity, range(10)))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    '''
    return e


def pred_negate(predicate: Callable[..., bool]) -> Callable[..., bool]:
    '''
    Gives a function which returns the inverse of the argument predicate.

    >>> isodd = lambda x: x % 2 == 1
    >>> iseven = pred_negate(isodd)
    >>> iseven(10)
    True
    '''
    @wraps(predicate)
    def _impl(*args, **kwargs):
        return not predicate(*args, **kwargs)
    return _impl
