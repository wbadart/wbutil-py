#!/usr/bin/env python

'''
wbutil/pipeline.py

Helpers which wrap standard library threaded queue.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from collections import OrderedDict
from queue import Queue as StdQueue
from threading import Event, Lock, Thread
from uuid import uuid4

__all__ = [
    'Pipeline',
]


class Pipeline(object):
    '''
    Simplify the interface provided by standard library queue. Specifically
    tailored to processing lists of data.
    '''

    def __init__(self, func, maxsize=0, nthreads=4):
        self._q = StdQueue(maxsize)
        self._func = func

        self._threads = []
        for _ in range(nthreads):
            self._threads.append(Thread(target=self._worker))
        self._nthreads = nthreads

        self._results = OrderedDict()
        self._result_lock = Lock()
        self._events = {}

        # Track queue state; enforce one-time usage
        self._started = False
        self._stopped = False

    def _worker(self):
        while True:
            key, item, event = self._q.get()
            if key is None:
                self._q.task_done()
                break
            result = self._func(item)
            with self._result_lock:
                self._results[key] = result
            event.set()
            self._q.task_done()

    def __enter__(self):
        '''Start threads.'''
        if self._started:
            raise RuntimeError('Pipelines cannot be reused')
        self._started = True
        for thread in self._threads:
            thread.start()
        return self

    def __exit__(self, exception_t=Exception, exception=None, traceback=None):
        '''Stop and join the threads.'''
        for thread in self._threads:
            self._q.put((None, None, None))
        for thread in self._threads:
            thread.join()
        self._q.join()
        self._stopped = True

    def put(self, item, key=None):
        '''Add an item to apply func to.'''
        if self._stopped:
            raise RuntimeError('this Pipeline has already been stopped')
        if (key, item) != (None, None) and key is None:
            key = str(uuid4())
        e = Event()
        self._events[key] = e
        self._q.put((key, item, e))
        return key

    def get(self, key, timeout=None):
        '''Get the result from an individual item.'''
        self._events[key].wait(timeout)
        return self._results.get(key)

    def map(self, iterable):
        '''
        Apply Pipeline.func to each item in the argument iterable.
        '''
        if not self._started:
            self.start()
        for i, item in enumerate(iterable):
            self.put(item, key=i)
        self.shutdown()
        return [self._results[j] for j in range(i + 1)]

    @property
    def func(self):
        '''Allow user code to inspect (though not modify) func.'''
        return self._func

    # Nice aliases for context functions, for use when `with' not appropriate
    start = __enter__
    shutdown = __exit__
