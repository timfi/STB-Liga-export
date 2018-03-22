# -*- coding: utf-8 -*-
import inspect
from threading import RLock
from functools import wraps

__all__ = [
    'Singleton',
    'thread_safe',
    'create_reprs',
]


# taken from https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def thread_safe(cls):
    _lock = RLock()
    for name, attr in cls.__dict__.items():
        if callable(attr) and name != '__init__':
            @wraps(attr)
            def wrapper(*args, **kwargs):
                with _lock:
                    val = attr(*args, **kwargs)
                return val
            setattr(cls, name, wrapper)
    return cls


def create_reprs(cls):
    for name, attr in cls.__dict__.items():
        if inspect.isclass(attr) and '__tablename__' in attr.__dict__:
            def __repr__(self):
                return f'<{self.__name__} {str({key: getattr(self, key) for key, item in self.__dict__ if instanceof(item, Column)})}>'
            setattr(attr, '__repr__', __repr__)
    return cls
