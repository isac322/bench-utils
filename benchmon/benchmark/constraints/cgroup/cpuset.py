# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import BaseCgroupConstraint
from ....utils.cgroup import Cpuset

if TYPE_CHECKING:
    from .... import Context


class CpusetConstraint(BaseCgroupConstraint):
    """
    :mod:`~benchmon.benchmark.constraints.cgroup` 중에서 `cpuset` subsystem을 사용하는 constraint.

    현재 `cpuset.cpus` 와 `cpuset.mems` 를 조절 가능하다.
    """
    _group: Cpuset
    _cpus: Optional[str]
    _mems: Optional[str]

    def __init__(self, identifier: str, cpus: Optional[str], mems: Optional[str]) -> None:
        """
        :param cpus: `cpuset.cpus` 값. ``None`` 일경우 기본값 사용
        :type cpus: typing.Optional[str]
        :param mems: `cpuset.mems` 값. ``None`` 일경우 기본값 사용
        :type mems: typing.Optional[str]
        """
        self._group = Cpuset(identifier)
        self._cpus = cpus
        self._mems = mems

    @property
    def cpus(self) -> Optional[str]:
        """
        :return: `cpuset.cpus` 값. ``None`` 일경우 기본값 사용
        :rtype: typing.Optional[str]
        """
        return self._cpus

    @property
    def mems(self) -> Optional[str]:
        """
        :return: `cpuset.mems` 값. ``None`` 일경우 기본값 사용
        :rtype: typing.Optional[str]
        """
        return self._mems

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        if self._cpus is not None:
            await self._group.assign_cpus(self._cpus)
        if self._mems is not None:
            await self._group.assign_mems(self._mems)
