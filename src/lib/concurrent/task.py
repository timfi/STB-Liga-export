# -*- coding: utf-8 -*-
import logging
from typing import NamedTuple, Callable, List
from concurrent.futures import Future
from functools import wraps

from ..helpers import snake_to_camel

__all__ = [
    'make_task_factory',
    'TaskBase',
    'ToDo',
    'ToDos',
    'multiple_dispatch_callback',
]


def make_task_factory(func):
    """Decorator to create a task factory from method."""
    task_name = snake_to_camel(func.__name__ + '_task')

    class Task(TaskBase):
        def __init__(self, *init_args, **init_kwargs):
            super(Task, self).__init__(task_name)
            self._args = init_args
            self._kwargs = init_kwargs
            self._func = func

        def __call__(self, processor):
            return self._func(processor, *self._args, **self._kwargs)

    Task.__name__ = task_name

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Task(*args, **kwargs)

    return wrapper


class TaskBase:
    def __init__(self, task_name):
        self.logger = logging.getLogger(task_name)

    def __call__(self, processor):
        pass


ToDo = NamedTuple('ToDo', [('task', TaskBase), ('callback', Callable[[Future], None])])
ToDos = List[ToDo]


def multiple_dispatch_callback(*callbacks, chain=False):
    """A 'simple' callback to run multiple callbacks

    :param callbacks: callbacks to run
    :param chain: allows the chaining of results
    :return: the assembled callback
    """
    def callback(fut):
        for x in callbacks:
            val = x(fut)
            if chain:
                fut = Future()
                fut.set_result(val)
    return callback
