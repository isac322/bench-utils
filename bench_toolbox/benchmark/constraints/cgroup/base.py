# coding: UTF-8

from abc import ABCMeta

from ..base import BaseConstraint
from ....utils.cgroup.base import BaseCGroup


class BaseCgroupConstraint(BaseConstraint, metaclass=ABCMeta):
    _group: BaseCGroup

    async def on_init(self) -> None:
        await self._group.create_group()

    async def on_start(self) -> None:
        await self._group.rename(self._benchmark.group_name)

    async def on_destroy(self) -> None:
        await self._group.delete()

    @property
    def identifier(self) -> str:
        return self._group.identifier
