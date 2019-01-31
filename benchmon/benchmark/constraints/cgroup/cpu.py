# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type

from .base import BaseCgroupConstraint
from ..base_builder import BaseBuilder
from ....utils.cgroup import CPU

if TYPE_CHECKING:
    from ...base import BaseBenchmark


class CpuConstraint(BaseCgroupConstraint):
    """
    :mod:`~benchmon.benchmark.constraints.cgroup` 중에서 `cpu` subsystem을 사용하는 constraint.

    현재 `cpu.cfs_period_us` 와 `cpu.cfs_quota_us` 를 조절 가능하다.
    """
    _group: CPU
    _period: Optional[int]
    _quota: Optional[int]

    def __new__(cls: Type[CpuConstraint], bench: BaseBenchmark,
                period: Optional[int], quota: Optional[int]) -> CpuConstraint:
        """
        :param bench: 이 constraint가 붙여질 :class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>`
        :type bench: benchmon.benchmark.base.BaseBenchmark
        :param period: `cpu.cfs_period_us` 값. ``None`` 일경우 기본값 사용
        :type period: typing.Optional[int]
        :param quota: `cpu.cfs_quota_us` 값. ``None`` 일경우 기본값 사용
        :type quota: typing.Optional[int]
        """
        obj: CpuConstraint = super().__new__(cls, bench)

        obj._group = CPU(bench.group_name)
        obj._period = period
        obj._quota = quota

        return obj

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

    async def on_init(self) -> None:
        await super().on_init()

        if self._period is not None:
            await self._group.assign_period(self._period)
        if self._quota is not None:
            await self._group.assign_quota(self._quota)

    class Builder(BaseBuilder['CpuConstraint']):
        """ :class:`~benchmon.benchmark.constraints.cgroup.cpu.CpuConstraint` 를 객체화하는 빌더 """
        _period: Optional[int]
        _quota: Optional[int]

        def __init__(self, period: int = None, quota: int = None) -> None:
            """
            :param period: `cpu.cfs_period_us` 값. ``None`` 일경우 기본값 사용
            :type period: typing.Optional[int]
            :param quota: `cpu.cfs_quota_us` 값. ``None`` 일경우 기본값 사용
            :type quota: typing.Optional[int]
            """
            super().__init__()

            self._period = period
            self._quota = quota

        def finalize(self, benchmark: BaseBenchmark) -> CpuConstraint:
            return CpuConstraint.__new__(CpuConstraint, benchmark, self._period, self._quota)
