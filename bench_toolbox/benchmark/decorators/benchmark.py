# coding: UTF-8

from __future__ import annotations

import functools
from typing import Any, Callable, TYPE_CHECKING

# because of circular import
if TYPE_CHECKING:
    from ..launchable import Benchmark


# TODO: generalize or move into launchable.py


def ensure_running(func: Callable[[Benchmark, Any], Any]):
    @functools.wraps(func)
    def decorator(self: Benchmark, *args, **kwargs):
        if not self.is_running:
            raise RuntimeError(f'The benchmark ({self._identifier}) has already ended or never been invoked.'
                               ' Run benchmark first via invoking `run()`!')
        return func(self, *args, **kwargs)

    return decorator


def ensure_not_running(func: Callable[[Benchmark, Any], Any]):
    @functools.wraps(func)
    def decorator(self: Benchmark, *args, **kwargs):
        if self.is_running:
            raise RuntimeError(f'benchmark {self._bench_driver.pid} is already in running.')
        return func(self, *args, **kwargs)

    return decorator


# TODO: clarify purpose
def ensure_invoked(func: Callable[[Benchmark, Any], Any]):
    @functools.wraps(func)
    def decorator(self: Benchmark, *args, **kwargs):
        if not self._bench_driver.has_invoked:
            raise RuntimeError(f'benchmark {self._identifier} is never invoked.')
        return func(self, *args, **kwargs)

    return decorator
