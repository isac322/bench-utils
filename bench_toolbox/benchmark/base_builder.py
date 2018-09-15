# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar

from .base_benchmark import BaseBenchmark
from .constraints import BaseConstraint
from ..monitors import MonitorData
from ..monitors.base_builder import BaseBuilder as MonitorBuilder
from ..monitors.base_monitor import BaseMonitor

T = TypeVar('T', bound=BaseBenchmark)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool = False
    _cur_obj: Optional[T] = None
    _monitors: List[BaseMonitor[MonitorData]] = list()
    _constraints: Dict[Type[BaseConstraint], BaseConstraint] = dict()

    @abstractmethod
    def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
        pass

    def build_monitor(self, monitor_builder: MonitorBuilder) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        monitor = self._build_monitor(monitor_builder)
        self._monitors.append(monitor)

        required_constraint = monitor.required_constraint()
        if required_constraint is not None and required_constraint not in self._constraints:
            self._constraints[required_constraint] = required_constraint(self._cur_obj)

        return self

    @abstractmethod
    def _finalize(self) -> None:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()
        self._cur_obj._constraints = tuple(self._constraints.values())

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
