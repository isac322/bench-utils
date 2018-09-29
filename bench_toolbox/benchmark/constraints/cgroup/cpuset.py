# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type

from .base import BaseCgroupConstraint
from ..base_builder import BaseBuilder
from ....utils.cgroup import Cpuset

if TYPE_CHECKING:
    from ...base import BaseBenchmark


class CpusetConstraint(BaseCgroupConstraint):
    _group: Cpuset
    _cpus: Optional[str]
    _mems: Optional[str]

    def __new__(cls: Type[CpusetConstraint], bench: BaseBenchmark,
                cpus: Optional[str], mems: Optional[str]) -> CpusetConstraint:
        obj: CpusetConstraint = super().__new__(cls, bench)

        obj._group = Cpuset(bench.group_name)
        obj._cpus = cpus
        obj._mems = mems

        return obj

    @property
    def cpus(self) -> Optional[str]:
        return self._cpus

    @property
    def mems(self) -> Optional[str]:
        return self._mems

    async def on_init(self) -> None:
        await super().on_init()

        if self._cpus is not None:
            await self._group.assign_cpus(self._cpus)
        if self._mems is not None:
            await self._group.assign_mems(self._mems)

    class Builder(BaseBuilder['CpuConstraint']):
        _cpus: Optional[str]
        _mems: Optional[str]

        def __init__(self, cpus: Optional[str], mems: Optional[str]) -> None:
            super().__init__()

            self._cpus = cpus
            self._mems = mems

        def finalize(self, benchmark: BaseBenchmark) -> CpusetConstraint:
            return CpusetConstraint.__new__(CpusetConstraint, benchmark, self._cpus, self._mems)
