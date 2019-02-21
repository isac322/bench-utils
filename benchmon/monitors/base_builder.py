# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, Optional, TYPE_CHECKING, TypeVar

from .base import BaseMonitor

if TYPE_CHECKING:
    # because of circular import
    from ..benchmark import BaseBenchmark

T = TypeVar('T', bound=BaseMonitor)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool
    _cur_bench: Optional[BaseBenchmark]

    def __init__(self) -> None:
        self._is_finalized = False
        self._cur_bench = None

    def set_benchmark(self, bench: BaseBenchmark) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._cur_bench = bench

        return self

    @abstractmethod
    def _finalize(self) -> T:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        ret = self._finalize()

        self._is_finalized = True

        return ret
