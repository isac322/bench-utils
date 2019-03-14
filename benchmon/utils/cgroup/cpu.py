# coding: UTF-8

from typing import ClassVar

from .base import BaseCGroup
from ..asyncio_subprocess import check_run


class CPU(BaseCGroup):
    """
    `cgroup cpu subsystem <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html
    /resource_management_guide/sec-cpu>`_ 를 대표하는 클래스.
    """
    CONTROLLER_NAME: ClassVar[str] = 'cpu'

    async def assign_quota(self, quota: int) -> None:
        """
        `cpu.cfs_quota_us` 를 설정한다.

        :param quota: 설정할 `cfs_quota_us` 값
        :type quota: int
        """
        await check_run('cgset', '-r', f'cpu.cfs_quota_us={quota}', self._name)

    async def assign_period(self, period: int) -> None:
        """
        `cpu.cfs_period_us` 를 설정한다.

        :param period: 설정할 `cfs_period_us` 값
        :type period: int
        """
        await check_run('cgset', '-r', f'cpu.cfs_period_us={period}', self._name)
