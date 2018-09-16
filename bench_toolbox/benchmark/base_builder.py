# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar

from .base_benchmark import BaseBenchmark
from .constraints.base import BaseConstraint
from .constraints.base_builder import BaseBuilder as ConstraintBuilder
from ..monitors import MonitorData
from ..monitors.base_builder import BaseBuilder as MonitorBuilder
from ..monitors.base_monitor import BaseMonitor

T = TypeVar('T', bound=BaseBenchmark)
_CT = TypeVar('_CT', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool = False
    _cur_obj: Optional[T] = None
    _monitors: List[BaseMonitor[MonitorData]] = list()
    # TODO: change key type to _CT not ConstraintBuilder[_CT]
    _constraint_builders: Dict[Type[ConstraintBuilder[_CT]], ConstraintBuilder[_CT]] = dict()

    @abstractmethod
    def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
        pass

    def build_monitor(self, monitor_builder: MonitorBuilder) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        monitor = self._build_monitor(monitor_builder)
        self._monitors.append(monitor)

        required_constraint_builder = monitor.required_constraint()
        if required_constraint_builder is not None \
                and type(required_constraint_builder) not in self._constraint_builders:
            self._constraint_builders[type(required_constraint_builder)] = required_constraint_builder

        return self

    @abstractmethod
    def _finalize(self) -> None:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()
        self._cur_obj._constraints = tuple(map(lambda x: x.finalize(self._cur_obj), self._constraint_builders.values()))

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
