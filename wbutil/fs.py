#!/usr/bin/env python

'''
wbutil/fs.py

Filesystem utilities.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from typing import Callable


def saveobj(constructor: Callable, path: str):
    '''
    Construct an object and save it to the disk for later use. Useful for
    objects with expensive constructors such as ones that include Web requests
    since they're only run if the storage file doesn't already exist.

    >>> from functools import partial; from requests import get
    >>> req = objstorage(partial(get, 'http://example.com'), 'myreq.pickle')
    >>> req
    <Response [200]>
    '''
    from os.path import exists
    from pickle import dump, load
    if not exists(path):
        obj = constructor()
        with open(path, 'wb') as fs:
            dump(obj, fs)
    else:
        with open(path, 'rb') as fs:
            obj = load(fs)
    return obj
