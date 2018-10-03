# coding: UTF-8

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, Tuple, Type

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ...utils import ResCtrl

if TYPE_CHECKING:
    from ..base import BaseBenchmark


class ResCtrlConstraint(BaseConstraint):
    _masks: Tuple[str, ...]
    _group: ResCtrl

    def __new__(cls: Type[ResCtrlConstraint], bench: BaseBenchmark, masks: Tuple[str, ...]) -> ResCtrlConstraint:
        obj: ResCtrlConstraint = super().__new__(cls, bench)

        obj._masks = masks
        obj._group = ResCtrl()

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def on_start(self) -> None:
        self._group.group_name = self._benchmark.group_name

        await self._group.create_group()

        if len(self._masks) is not 0:
            await self._group.assign_llc(*self._masks)

        children = self._benchmark.all_child_tid()
        await self._group.add_tasks(children)

    async def on_destroy(self) -> None:
        try:
            await self._group.delete()
        except PermissionError:
            pass

    class Builder(BaseBuilder['ResCtrlConstraint']):
        _masks: Tuple[str, ...] = tuple()

        def __init__(self, masks: Iterable[str] = tuple()) -> None:
            self._masks = masks

        def finalize(self, benchmark: BaseBenchmark) -> ResCtrlConstraint:
            return ResCtrlConstraint.__new__(ResCtrlConstraint, benchmark, self._masks)
