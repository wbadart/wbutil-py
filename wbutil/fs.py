#!/usr/bin/env python

'''
wbutil/fs.py

Filesystem utilities.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from contextlib import closing
from os.path import exists
from pickle import dump, load
from typing import Any, Callable, TextIO

__all__ = [
    'saveobj',
    'tryopen',
]


def saveobj(constructor: Callable[[], Any], path: str) -> Any:
    '''
    Construct an object and save it to the disk for later use. Useful for
    objects with expensive constructors such as ones that include Web requests
    since they're only run if the storage file doesn't already exist.

    >>> from functools import partial; from requests import get
    >>> req = objstorage(partial(get, 'http://example.com'), 'myreq.pickle')
    >>> req
    <Response [200]>
    '''
    if not exists(path):
        obj = constructor()
        with open(path, 'wb') as fs:
            dump(obj, fs)
    else:
        with open(path, 'rb') as fs:
            obj = load(fs)
    return obj


def tryopen(
        path: str,
        process: Callable[[TextIO], Any]=lambda fs: fs.read(),
        default: Any=None) -> Any:
    '''
    Attempt to open the file at `path`, process it, and close it. If file
    cannot be loaded, the default value is returned. Does not swallow errors
    from the processing function.

    >>> from json import load
    >>> data = try_open('data.json', process=load, default={})
    >>> data
    {'my': 'data'}
    >>> description = try_open('doesnt_exist.txt', default='No description')
    >>> description
    'No description'
    '''
    try:
        fs = open(path)
    except OSError as e:
        if default is not None:
            return default
        else:
            msg = ('an error occurred opening {!r}. '
                   'Provide a non-None argument `default\' to suppress')
            raise OSError(msg.format(path)) from e
    with closing(fs):
        return process(fs)
