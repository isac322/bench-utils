# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Callable, Coroutine, Generic, Optional, TYPE_CHECKING, TypeVar

from .base import BaseMonitor

if TYPE_CHECKING:
    from .messages.base import BaseMessage
    # because of circular import
    from ..benchmark import BaseBenchmark

T = TypeVar('T', bound=BaseMonitor)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool
    _cur_bench: Optional[BaseBenchmark]
    _cur_emitter: Callable[[BaseMessage], Coroutine[None, None, None]]

    def __init__(self) -> None:
        self._is_finalized = False
        self._cur_bench = None
        self._cur_emitter = None

    def set_benchmark(self, bench: BaseBenchmark) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._cur_bench = bench

        return self

    def set_emitter(self, emitter: Callable[[BaseMessage], Coroutine[None, None, None]]) -> BaseBuilder[T]:
        self._cur_emitter = emitter

        return self

    @abstractmethod
    def _finalize(self) -> T:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')
        if self._cur_emitter is None:
            raise ValueError('emitter is not set')

        ret = self._finalize()

        self._is_finalized = True

        return ret
