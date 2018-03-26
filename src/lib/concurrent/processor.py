# -*- coding: utf-8 -*-
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import RLock

from .task import multiple_dispatch_callback, ToDo, ToDos

__all__ = [
    'ConcurrentProcessor',
]


class ConcurrentProcessor:
    def __init__(self, *, max_workers=8):
        self._logger = logging.getLogger(self.__class__.__qualname__)

        self._logger.info('Starting ThreadPoolExecutor...')
        self._worker_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = RLock()
        self._resource = None

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return getattr(self._resource, item)

    def quit(self):
        with self._lock:
            self._logger.info('Deleting ConcurrentProcessor...')
            self._worker_pool.shutdown()

    def do(self, task, *callbacks, chain_callbacks=False):
        """A method to submit a task request and callback to the drivers worker pool.

        :param task: task to do
        :param callbacks: multiple callbacks to run on result
        :param chain_callbacks: used to pass result from one callback to the next
        """
        if len(callbacks):
            self._do(ToDo(task, multiple_dispatch_callback(*callbacks, chain=chain_callbacks)))
        else:
            self._do(ToDo(task, lambda fut: self._logger.debug(f"Doing nothing with {fut}")))

    def _do_multiple(self, todos):
        """A methode to do multiple todos

        :param todos:
        """
        assert isinstance(todos, ToDos), 'Can only do ToDos...'
        for todo in todos:
            self._do(todo)

    def _do(self, todo):
        """A methode to submit a todo object to the worker pool

        :param todo: the todo to do
        """
        assert isinstance(todo, ToDo), 'Can only do ToDos...'
        fut = self._worker_pool.submit(todo.task, self)
        fut.add_done_callback(todo.callback)