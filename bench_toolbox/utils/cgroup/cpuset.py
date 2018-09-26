# coding: UTF-8

import asyncio
from typing import ClassVar

from .base import BaseCGroup


class Cpuset(BaseCGroup):
    CONTROLLER_NAME: ClassVar[str] = 'cpuset'

    async def assign_cpus(self, core_ids: str) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpuset.cpus={core_ids}', self._name)
        await proc.communicate()

    async def assign_mems(self, socket_ids: str) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpuset.mems={socket_ids}', self._name)
        await proc.communicate()
