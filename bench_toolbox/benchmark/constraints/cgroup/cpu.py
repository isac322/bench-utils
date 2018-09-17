# coding: UTF-8

from __future__ import annotations

from typing import Optional, Type

from .base import BaseCgroupConstraint
from ..base_builder import BaseBuilder
from ....utils.cgroup.cpu import CPU


class CpuConstraint(BaseCgroupConstraint):
    _group: CPU
    _period: Optional[int]
    _quota: Optional[int]

    def __new__(cls: Type[CpuConstraint], bench: 'BaseBenchmark',
                period: Optional[int], quota: Optional[int]) -> CpuConstraint:
        obj: CpuConstraint = super().__new__(cls, bench)

        obj._group = CPU(bench.group_name)
        obj._period = period
        obj._quota = quota

        return obj

    @property
    def period(self) -> Optional[int]:
        return self._period

    @property
    def quota(self) -> Optional[int]:
        return self._quota

    async def on_init(self) -> None:
        await super().on_init()

        if self._period is not None:
            await self._group.assign_period(self._period)
        if self._quota is not None:
            await self._group.assign_quota(self._quota)

    class Builder(BaseBuilder['CpuConstraint']):
        _period: Optional[int]
        _quota: Optional[int]

        def __init__(self, period: int = None, quota: int = None) -> None:
            super().__init__()

            self._period = period
            self._quota = quota

        def finalize(self, benchmark: 'BaseBenchmark') -> CpuConstraint:
            return CpuConstraint.__new__(CpuConstraint, benchmark, self._period, self._quota)
