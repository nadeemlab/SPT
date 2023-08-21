"""Simple, naive caching with undefined eviction that works on instance methods by ignoring self."""

from functools import wraps

__shared_simple_cache__: dict = {}

def simple_instance_method_cache(maxsize=1000):
    def decorator(func):
        if func.__name__ not in __shared_simple_cache__:
            __shared_simple_cache__[func.__name__] = {}
        @wraps(func)
        def wrapped_func(self, *args):
            if args in __shared_simple_cache__[func.__name__]:
                return __shared_simple_cache__[func.__name__][args]
            result = func(self, *args)
            if len(__shared_simple_cache__[func.__name__]) >= maxsize:
                key = list(__shared_simple_cache__[func.__name__].keys())[0]
                del __shared_simple_cache__[func.__name__][key]
            __shared_simple_cache__[func.__name__][args] = result
            return result
        return wrapped_func
    return decorator
