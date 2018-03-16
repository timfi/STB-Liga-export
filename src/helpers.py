from threading import RLock


# taken from https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def threadsafe(cls):
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
