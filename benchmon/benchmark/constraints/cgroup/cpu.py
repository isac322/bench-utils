# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import BaseCgroupConstraint
from ....utils.cgroup import CPU

if TYPE_CHECKING:
    from .... import Context


class CpuConstraint(BaseCgroupConstraint):
    """
    :mod:`~benchmon.benchmark.constraints.cgroup` 중에서 `cpu` subsystem을 사용하는 constraint.

    현재 `cpu.cfs_period_us` 와 `cpu.cfs_quota_us` 를 조절 가능하다.
    """
    _group: CPU
    _period: Optional[int]
    _quota: Optional[int]

    def __init__(self, identifier: str, period: Optional[int], quota: Optional[int]) -> None:
        """
        :param period: `cpu.cfs_period_us` 값. ``None`` 일경우 기본값 사용
        :type period: typing.Optional[int]
        :param quota: `cpu.cfs_quota_us` 값. ``None`` 일경우 기본값 사용
        :type quota: typing.Optional[int]
        """
        self._group = CPU(identifier)
        self._period = period
        self._quota = quota

    @property
    def period(self) -> Optional[int]:
        """
        :return: `cpu.cfs_period_us` 값. ``None`` 일경우 기본값 사용
        :rtype: typing.Optional[int]
        """
        return self._period

    @property
    def quota(self) -> Optional[int]:
        """
        :return: `cpu.cfs_quota_us` 값. ``None`` 일경우 기본값 사용
        :rtype: typing.Optional[int]
        """
        return self._quota

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        if self._period is not None:
            await self._group.assign_period(self._period)
        if self._quota is not None:
            await self._group.assign_quota(self._quota)
