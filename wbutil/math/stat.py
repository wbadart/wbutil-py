#!/usr/bin/env python

'''
wbutil/math/stat.py

Various utilities for descriptive statistics.

Will Badart <wbadart@live.com>
created: FEB 2018
'''

from numbers import Real
from typing import Sequence

__all__ = [
    'mean',
    'median',
    'variance',
    'std',
]


def mean(a: Sequence[Real]) -> float:
    '''
    Return the mean of a list of numbers.

    >>> mean([1, 2, 3, 4])
    2.5
    '''
    return sum(a) / len(a)


def median(a: Sequence[Real]) -> float:
    '''
    Return the median of a list of numbers.

    >>> median([4, 6, 1])
    4
    >>> median([1, 1, 2, 3])
    1.5
    '''
    if _isodd(len(a)):
        return float(sorted(a)[len(a) // 2])
    else:
        return mean(sorted(a)[len(a) // 2 - 1:len(a) // 2 + 1])


def variance(a: Sequence[Real]) -> float:
    '''
    Get the variance (average squared distance to the mean) of a number list.

    >>> variance([1, 2, 3])
    0.6666666666666666
    >>> variance([1, 1, 1, 1])
    1.0
    '''
    avg = mean(a)
    return mean([(avg - e) ** 2 for e in a])


def std(a: Sequence[Real]) -> float:
    '''
    Gives the standard deviation of a list of numbers (sqrt(variance)).
    '''
    return variance(a) ** 0.5


def _isodd(n):
    return n % 2 != 0
