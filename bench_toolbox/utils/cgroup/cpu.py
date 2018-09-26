# coding: UTF-8

import asyncio
from typing import ClassVar

from .base import BaseCGroup


class CPU(BaseCGroup):
    CONTROLLER_NAME: ClassVar[str] = 'cpu'

    async def assign_quota(self, quota: int) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_quota_us={quota}', self._name)
        await proc.communicate()

    async def assign_period(self, period: int) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpu.cfs_period_us={period}', self._name)
        await proc.communicate()
