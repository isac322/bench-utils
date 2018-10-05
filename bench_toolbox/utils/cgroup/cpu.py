# coding: UTF-8

from typing import ClassVar

from .base import BaseCGroup
from ..asyncio_subprocess import check_run


class CPU(BaseCGroup):
    CONTROLLER_NAME: ClassVar[str] = 'cpu'

    async def assign_quota(self, quota: int) -> None:
        await check_run('cgset', '-r', f'cpu.cfs_quota_us={quota}', self._name)

    async def assign_period(self, period: int) -> None:
        await check_run('cgset', '-r', f'cpu.cfs_period_us={period}', self._name)
