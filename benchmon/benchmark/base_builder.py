# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from typing import Dict, Generic, List, TYPE_CHECKING, Type, TypeVar

from .base import BaseBenchmark
from .constraints.base import BaseConstraint
from ..monitors.idle import IdleMonitor

if TYPE_CHECKING:
    from ..monitors import BaseMonitor, MonitorData
    from ..monitors.messages.handlers import BaseHandler

T = TypeVar('T', bound=BaseBenchmark)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    _is_finalized: bool = False
    _cur_obj: T
    _monitors: List[BaseMonitor[MonitorData]]
    _constraints: Dict[Type[BaseConstraint], BaseConstraint]

    def __init__(self) -> None:
        self._monitors = list()
        self._constraints = dict()

    def add_handler(self, handler: BaseHandler) -> T.Builder:
        self._cur_obj._pipeline.add_handler(handler)
        return self

    def add_monitor(self, monitor: BaseMonitor) -> BaseBuilder[T]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._monitors.append(monitor)

        return self

    def add_constraint(self, constraint: BaseConstraint) -> BaseBuilder[T]:
        # TODO: warning when duplicated type of constraint is added
        self._constraints[type(constraint)] = constraint
        return self

    def _finalize(self) -> None:
        if len(self._monitors) is 0:
            self.add_monitor(IdleMonitor())

    def finalize(self) -> T:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()

        self._cur_obj._monitors = self._monitors
        self._cur_obj._constraints = tuple(self._constraints.values())

        # noinspection PyProtectedMember
        self._cur_obj._context_variable = self._cur_obj._initialize_context()

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
