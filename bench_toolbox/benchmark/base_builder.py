# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar

from .base import BaseBenchmark
from .constraints import BaseBuilder as ConstraintBuilder, BaseConstraint
from ..monitors import BaseBuilder as MonitorBuilder, BaseMonitor, MonitorData

T = TypeVar('T', bound=BaseBenchmark)
_CT = TypeVar('_CT', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool = False
    _cur_obj: Optional[T] = None
    _monitors: List[BaseMonitor[MonitorData]]
    # TODO: change key type to _CT not ConstraintBuilder[_CT]
    _constraint_builders: Dict[Type[ConstraintBuilder[_CT]], _CT]

    def __init__(self) -> None:
        self._monitors = list()
        self._constraint_builders = dict()

    @abstractmethod
    def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
        pass

    def build_monitor(self, monitor_builder: MonitorBuilder) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        monitor = self._build_monitor(monitor_builder)
        self._monitors.append(monitor)

        return self

    def build_constraint(self, constraint_builder: ConstraintBuilder) -> BaseBuilder[T]:
        self._constraint_builders[type(constraint_builder)] = constraint_builder.finalize(self._cur_obj)
        return self

    @abstractmethod
    def _finalize(self) -> None:
        pass

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()

        self._cur_obj._monitors = self._monitors
        self._cur_obj._constraints = tuple(self._constraint_builders.values())

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
