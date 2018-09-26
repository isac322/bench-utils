# coding: UTF-8

from __future__ import annotations

import functools
from typing import Any, Callable, TYPE_CHECKING

# because of circular import
if TYPE_CHECKING:
    from ..drivers import BenchDriver


# TODO: generalize or move into benchmark.py


def ensure_running(func: Callable[[BenchDriver, Any], Any]):
    @functools.wraps(func)
    def decorator(self: BenchDriver, *args, **kwargs):
        if not self.is_running:
            raise RuntimeError(f'The benchmark ({self._name}) has already ended or never been invoked.'
                               ' Run benchmark first via invoking `run()`!')
        return func(self, *args, **kwargs)

    return decorator


def ensure_not_running(func: Callable[[BenchDriver, Any], Any]):
    @functools.wraps(func)
    def decorator(self: BenchDriver, *args, **kwargs):
        if self.is_running:
            raise RuntimeError(f'The benchmark ({self._name}) has already ended or never been invoked.'
                               ' Run benchmark first via invoking `run()`!')
        return func(self, *args, **kwargs)

    return decorator


def ensure_invoked(func: Callable[[BenchDriver, Any], Any]):
    @functools.wraps(func)
    def decorator(self: BenchDriver, *args, **kwargs):
        if not self.has_invoked:
            raise RuntimeError(f'The benchmark ({self._name}) has never been invoked.'
                               ' Run benchmark first via invoking `run()`!')
        return func(self, *args, **kwargs)

    return decorator
