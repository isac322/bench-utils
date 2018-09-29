# coding: UTF-8

from __future__ import annotations

from typing import Tuple, Type

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ..base import BaseBenchmark
from ...utils import ResCtrl


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
        await self._group.delete()

    class Builder(BaseBuilder['ResCtrlConstraint']):
        _masks: Tuple[str, ...] = tuple()

        def __init__(self, masks: Tuple[str, ...] = tuple()) -> None:
            self._masks = masks

        def finalize(self, benchmark: BaseBenchmark) -> ResCtrlConstraint:
            return ResCtrlConstraint.__new__(ResCtrlConstraint, benchmark, self._masks)
