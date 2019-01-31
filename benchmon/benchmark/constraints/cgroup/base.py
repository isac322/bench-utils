# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING

from ..base import BaseConstraint

if TYPE_CHECKING:
    from ....utils.cgroup.base import BaseCGroup


class BaseCgroupConstraint(BaseConstraint, metaclass=ABCMeta):
    """
    :mod:`~bench_toolbox.benchmark.constraints.cgroup` 에 속한 constraint들이 모두 공유하는 공통 부분을 묶어놓은 추상 클래스
    """
    _group: BaseCGroup

    async def on_init(self) -> None:
        await self._group.create_group()

    async def on_start(self) -> None:
        await self._group.rename(self._benchmark.group_name)

    async def on_destroy(self) -> None:
        await self._group.delete()

    @property
    def identifier(self) -> str:
        """
        이 constraint가 사용하는 cgroup의 group이름을 반환한다

        :return: 그룹이름
        :rtype: str
        """
        return self._group.identifier
