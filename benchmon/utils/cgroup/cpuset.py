# coding: UTF-8

from typing import ClassVar

from .base import BaseCGroup
from ..asyncio_subprocess import check_run


class Cpuset(BaseCGroup):
    """
    `cgroup cpuset subsystem <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html
    /resource_management_guide/sec-cpuset>`_ 를 대표하는 클래스.
    """
    CONTROLLER_NAME: ClassVar[str] = 'cpuset'

    async def assign_cpus(self, core_ids: str) -> None:
        """
        `cpuset.cpus` 를 설정한다.

        :param core_ids: 설정할 `cpus` 값
        :type core_ids: str
        """
        await check_run('cgset', '-r', f'cpuset.cpus={core_ids}', self._name)

    async def assign_mems(self, socket_ids: str) -> None:
        """
        `cpuset.mems` 를 설정한다.

        :param socket_ids: 설정할 `mems` 값
        :type socket_ids: str
        """
        await check_run('cgset', '-r', f'cpuset.mems={socket_ids}', self._name)
