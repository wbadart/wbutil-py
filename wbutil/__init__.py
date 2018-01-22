#!/usr/bin/env python

from . import func
from . import fs


def uniq(a):
    '''
    Generate the argument iterator with the duplicate members removed.

    >>> list(uniq([1, 2, 2, 3]))
    [1, 2, 3]
    '''
    seen = set()
    for e in a:
        if e not in seen:
            seen.add(e)
            yield e
        else:
            continue
