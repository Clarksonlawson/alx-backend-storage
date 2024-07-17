#!/usr/bin/env python3
"""
This module defines the Cache class to interact with Redis.
"""
import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator to count the number of calls to a method.

    :param method: The method to be decorated.
    :return: The decorated method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrapper function that increments the call count"""
        key = f"{method.__qualname__}:calls"
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator to store the history of inputs and outputs for a method.

    :param method: The method to be decorated.
    :return: The decorated method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrapper function to store call history"""
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


def replay(method: Callable) -> None:
    """
    Display the history of calls of a particular function.

    :param method: The method whose call history is to be displayed.
    """
    cache = method.__self__
    input_key = f"{method.__qualname__}:inputs"
    output_key = f"{method.__qualname__}:outputs"
    inputs = cache._redis.lrange(input_key, 0, -1)
    outputs = cache._redis.lrange(output_key, 0, -1)
    print(f"{method.__qualname__} was called {len(inputs)} times:")
    for input_data, output_data in zip(inputs, outputs):
        print(f"{method.__qualname__}(*{input_data.decode('utf-8')}) -> {output_data.decode('utf-8')}")


class Cache:
    """Cache class to interact with Redis"""

    def __init__(self):
        """Initialize the Cache with a Redis client and flush the database"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store the given data in Redis using a randomly generated key.

        :param data: Data to be stored in Redis.
        :return: The generated key as a string.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis and optionally apply a conversion function.

        :param key: The key to retrieve from Redis.
        :param fn: Optional function to convert the data.
        :return: The retrieved data, potentially converted by `fn`.
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn:
            return fn(data)
        return data

    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieve a string from Redis.

        :param key: The key to retrieve from Redis.
        :return: The retrieved string.
        """
        return self.get(key, lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieve an integer from Redis.

        :param key: The key to retrieve from Redis.
        :return: The retrieved integer.
        """
        return self.get(key, lambda d: int(d))

