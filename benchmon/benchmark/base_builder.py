# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from typing import Dict, Generic, List, TYPE_CHECKING, Type, TypeVar

from .base import BaseBenchmark
from .constraints.base import BaseConstraint
from ..monitors.idle import IdleMonitor

if TYPE_CHECKING:
    from .constraints import BaseBuilder as ConstraintBuilder
    from ..monitors import BaseBuilder as MonitorBuilder, BaseMonitor, MonitorData
    from ..monitors.messages.handlers import BaseHandler

_BT = TypeVar('_BT', bound=BaseBenchmark)
_CT = TypeVar('_CT', bound=BaseConstraint)


class BaseBuilder(Generic[_BT], metaclass=ABCMeta):
    _is_finalized: bool = False
    _cur_obj: _BT
    _monitors: List[BaseMonitor[MonitorData]]
    # TODO: change key type to _CT not ConstraintBuilder[_CT]
    _constraint_builders: Dict[Type[ConstraintBuilder[_CT]], _CT]

    def __init__(self) -> None:
        self._monitors = list()
        self._constraint_builders = dict()

    def add_handler(self, handler: BaseHandler) -> _BT.Builder:
        # noinspection PyProtectedMember
        self._cur_obj._pipeline.add_handler(handler)
        return self

    def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
        # noinspection PyProtectedMember
        return monitor_builder \
            .set_benchmark(self._cur_obj) \
            .set_emitter(self._cur_obj._pipeline.on_message) \
            .finalize()

    def build_monitor(self, monitor_builder: MonitorBuilder) -> BaseBuilder[_BT]:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        monitor = self._build_monitor(monitor_builder)
        self._monitors.append(monitor)

        return self

    def build_constraint(self, constraint_builder: ConstraintBuilder) -> BaseBuilder[_BT]:
        self._constraint_builders[type(constraint_builder)] = constraint_builder.finalize(self._cur_obj)
        return self

    def _finalize(self) -> None:
        if len(self._monitors) is 0:
            self.build_monitor(IdleMonitor.Builder())

    def finalize(self) -> _BT:
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()

        self._cur_obj._monitors = tuple(self._monitors)
        self._cur_obj._constraints = tuple(self._constraint_builders.values())

        ret, self._cur_obj = self._cur_obj, None
        self._is_finalized = True

        return ret
