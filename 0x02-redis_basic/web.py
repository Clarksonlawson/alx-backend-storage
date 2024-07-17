#!/usr/bin/env python3
"""
This module defines the get_page function to fetch HTML content and cache it using Redis.
"""
import redis
import requests
from typing import Callable
from functools import wraps


def cache_with_expiration(expiration: int):
    """
    Decorator to cache the result of a function with an expiration time.

    :param expiration: Time in seconds for the cache to expire.
    :return: The decorated function.
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            url = args[0]
            cache_key = f"cache:{url}"
            cached_result = self._redis.get(cache_key)
            if cached_result:
                return cached_result.decode('utf-8')

            result = method(self, *args, **kwargs)
            self._redis.setex(cache_key, expiration, result)
            return result
        return wrapper
    return decorator


def count_url_access(method: Callable) -> Callable:
    """
    Decorator to count how many times a URL has been accessed.

    :param method: The method to be decorated.
    :return: The decorated method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        url = args[0]
        count_key = f"count:{url}"
        self._redis.incr(count_key)
        return method(self, *args, **kwargs)
    return wrapper


class Cache:
    """Cache class to interact with Redis"""

    def __init__(self):
        """Initialize the Cache with a Redis client"""
        self._redis = redis.Redis()

    @count_url_access
    @cache_with_expiration(10)
    def get_page(self, url: str) -> str:
        """
        Fetch the HTML content of a given URL and cache it.

        :param url: The URL to fetch.
        :return: The HTML content of the URL.
        """
        response = requests.get(url)
        return response.text

