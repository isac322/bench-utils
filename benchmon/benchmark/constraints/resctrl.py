# coding: UTF-8

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, Tuple

from .base import BaseConstraint
from ..base import BaseBenchmark
from ...utils import ResCtrl

if TYPE_CHECKING:
    from ... import Context


class ResCtrlConstraint(BaseConstraint):
    """
    :class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 의 실행 직후에 해당 벤치마크가 사용할 수 있는 최대 LLC를
    resctrl를 통해 입력받은 값으로 제한하며, 벤치마크의 실행이 종료될 경우 그 resctrl 그룹을 삭제한다.
    """
    _masks: Tuple[str, ...]
    _group: ResCtrl

    def __init__(self, masks: Iterable[str]) -> None:
        """
        :param masks: CPU 소켓별로 할당할 LLC mask
        :type masks: typing.Iterable[str]
        """
        self._masks = tuple(masks)
        self._group = ResCtrl()

    async def on_start(self, context: Context) -> None:
        benchmark = BaseBenchmark.of(context)

        self._group.group_name = benchmark.group_name

        await self._group.create_group()

        if len(self._masks) is not 0:
            await self._group.assign_llc(*self._masks)

        children = benchmark.all_child_tid()
        await self._group.add_tasks(children)

    async def on_destroy(self, context: Context) -> None:
        try:
            await self._group.delete()
        except PermissionError:
            pass
