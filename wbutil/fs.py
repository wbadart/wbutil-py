#!/usr/bin/env python

'''
wbutil/fs.py

Filesystem utilities.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from contextlib import closing
from json import dumps, loads
from os import PathLike
from os.path import exists
from pickle import dump, load
from typing import Any, Callable, TextIO, Union

__all__ = [
    'saveobj',
    'tryopen',
    'PersistentDict',
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


class PersistentDict(dict):
    '''
    A dict subclass, objects of which are directly linked to a file. That is to
    say, it provides methods for loading and saving self to and from a file.

    Provides a context manager interface so that data will be saved even if an
    exception is thrown in processing.

    Serialization protocol is JSON by default, but you can use any encoding
    that sends a dictionary to a string (e.g. YAML, pickle).
    '''

    def __init__(
            self,
            *args: Any,
            path: Union[str, PathLike]=None,
            encode: Callable[[dict], str]=dumps,
            usebytes: bool=False) -> None:
        '''
        Initialize like an ordinary dictionary, but provide the keyword-only
        arguments `path' (the file liked to this object) and `encode' (the
        function which serializes this object into a string to write to disk,
        defaults to `json.dumps').

        Set the `usebytes' flag in the constructor if your protocol expects
        bytes objects rather than strings.

        Assumes `path' is fresh. Use classmethod `from_path' to start with data
        loaded.
        '''
        if path is None:
            raise ValueError('cannot use PersistentDict without a save path')
        super().__init__(*args)
        self.path = path
        self.encode = encode
        self.mode = 'b' if usebytes else ''

    def __enter__(self) -> 'PersistentDict':
        return self

    def __exit__(
            self,
            exception_t=Exception,
            exception=None,
            traceback=None) -> None:
        '''
        Save the object when context is exited (throw away return value).
        '''
        self.save()

    def save(self) -> int:
        '''
        Write self's data to disk. Returns the result of `file.write' (total
        bytes written to disk).
        '''
        with open(self.path, 'w' + self.mode) as fs:
            return fs.write(self.encode(self))

    @classmethod
    def from_path(
            cls,
            path: Union[str, PathLike],
            encode: Callable[[dict], str]=dumps,
            decode: Callable[[str], dict]=loads,
            usebytes: bool=False) -> 'PersistentDict':
        '''
        Instantiate a PersistentDict from an existing data file. Arguments
        follow the same semantics as PersistentDict.__init__, and `decode'
        should be the inverse of `encode'.
        '''
        with open(path, 'rb' if usebytes else 'r') as fs:
            obj = decode(fs.read())
        return cls(obj, path=path, encode=encode, usebytes=usebytes)
