# coding: UTF-8

from typing import Tuple

from .base import BaseConstraint
# FIXME: circular import
# from ..benchmark import BaseBenchmark
from ...utils import ResCtrl


class ResCtrlConstraint(BaseConstraint):
    _masks: Tuple[str, ...]
    _group: ResCtrl = ResCtrl()

    # noinspection PyUnresolvedReferences
    def __init__(self, bench: 'BaseBenchmark', *masks: str) -> None:
        super().__init__(bench)

        self._masks = masks

    async def on_start(self) -> None:
        self._group.group_name = self._benchmark.group_name

        if len(self._masks) is not 0:
            await self._group.assign_llc(*self._masks)

        await self._group.create_group()

        children = self._benchmark.all_child_tid()
        await self._group.add_tasks(children)

    async def on_destroy(self) -> None:
        await self._group.delete()
