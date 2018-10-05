# coding: UTF-8

from typing import ClassVar

from .base import BaseCGroup
from ..asyncio_subprocess import check_run


class Cpuset(BaseCGroup):
    CONTROLLER_NAME: ClassVar[str] = 'cpuset'

    async def assign_cpus(self, core_ids: str) -> None:
        await check_run('cgset', '-r', f'cpuset.cpus={core_ids}', self._name)

    async def assign_mems(self, socket_ids: str) -> None:
        await check_run('cgset', '-r', f'cpuset.mems={socket_ids}', self._name)
