# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, List, Optional, TypeVar

from .base_benchmark import BaseBenchmark
from ..monitors import MonitorData
from ..monitors.base_builder import BaseBuilder as MonitorBuilder
from ..monitors.base_monitor import BaseMonitor

T = TypeVar('T', bound=BaseBenchmark)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    def __init__(self) -> None:
        self._is_finalized = False
        self._cur_obj: Optional[T] = None
        self._monitors: List[BaseMonitor[MonitorData]] = list()

    @abstractmethod
    def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
        pass

    def build_monitor(self, monitor_builder: MonitorBuilder) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        monitor = self._build_monitor(monitor_builder)
        self._monitors.append(monitor)

        return self

    @abstractmethod
    def _finalize(self) -> None:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
