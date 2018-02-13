#!/usr/bin/env python

'''
wbutil/queue.py

Helpers which wrap standard library threaded queue.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from queue import Queue as StdQueue
from threading import Thread

__all__ = [
    # 'Queue',
]


class Queue(StdQueue):
    '''
    Simplify the interface provided by standard library queue. Specifically
    tailored to processing lists of data.
    '''

    def __init__(self, func, maxsize=0, nthreads=4):
        super().__init__(maxsize)
        self._func = func
        self._results = {}
        self._threads = [None] * nthreads
        self._nthreads = nthreads

    def _worker(self):
        while True:
            key, item = self.get()
            if item is None:
                break
            self._results[key] = self._func(item)
            self.task_done()

    def __enter__(self):
        '''Start threads.'''
        for i in range(self._nthreads):
            self._threads[i] = Thread(target=self._worker)
            self._threads[i].start()
        return self

    def __exit__(self, exception_t=Exception, exception=None, traceback=None):
        '''Stop and join the threads.'''
        for i in range(self._nthreads):
            self.put((0, None))
        for t in self._threads:
            t.join()

    def map(self, data_sequence):
        '''A special case where the result becomes a list.'''
        self._results = [None] * len(data_sequence)
        for item in enumerate(data_sequence):
            self.put(item)
        self.join()
        return self._results

    # Nice aliases for context functions, for use when `with' not appropriate
    start = __enter__
    shutdown = __exit__
