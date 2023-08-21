"""LRU cache implementation that works on instance methods."""

import functools
import weakref

def weak_lru(maxsize=128, typed=False):
    def wrapper(func):
        @functools.lru_cache(maxsize, typed)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)
        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)
        return inner
    return wrapper
