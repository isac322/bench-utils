# coding: UTF-8

import asyncio
from typing import ClassVar

import aiofiles

from .base import BaseCGroup


class CPU(BaseCGroup):
    CONTROLLER_NAME: ClassVar[str] = 'cpu'

    async def assign_quota(self, quota: int) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_quota_us={quota}', self._name)
        await proc.communicate()

    async def assign_period(self, period: int) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_period_us={period}', self._name)
        await proc.communicate()

    async def limit_cpu_quota(self, limit_percentage: float, period: int = None) -> None:
        if period is None:
            async with aiofiles.open(str(self.absolute_path() / 'cpu.cfs_period_us')) as afp:
                line: str = await afp.readline()
                period = int(line)

        cpu_cores = await self._get_cpu_affinity_from_group()
        quota = int(period * limit_percentage / 100 * len(cpu_cores))

        quota_proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_quota_us={quota}', self._name)
        await quota_proc.communicate()

        period_proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_period_us={period}', self._name)
        await period_proc.communicate()
