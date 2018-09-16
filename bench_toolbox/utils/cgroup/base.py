# coding: UTF-8

import asyncio
import getpass
import grp
import os
from abc import ABCMeta
from pathlib import Path
from typing import ClassVar, Iterable


class BaseCGroup(metaclass=ABCMeta):
    MOUNT_POINT: ClassVar[Path] = Path('/sys/fs/cgroup')
    CONTROLLER_NAME: ClassVar[str]

    _name: str

    def __init__(self, group_name: str) -> None:
        super().__init__()

        self._name = group_name

    @classmethod
    def absolute_path(cls) -> Path:
        return cls.MOUNT_POINT / cls.CONTROLLER_NAME

    @property
    def identifier(self) -> str:
        return f'{self.CONTROLLER_NAME}:{self._name}'

    async def create_group(self) -> None:
        uname: str = getpass.getuser()
        gid: int = os.getegid()
        gname: str = grp.getgrgid(gid).gr_name

        proc = await asyncio.create_subprocess_exec(
                'sudo', 'cgcreate', '-a', f'{uname}:{gname}', '-d', '755', '-f',
                '644', '-t', f'{uname}:{gname}', '-s', '644', '-g', self.identifier)
        await proc.communicate()

    async def chown(self, uid: int, gid: int) -> None:
        proc = await asyncio.create_subprocess_exec(
                'cgm', 'chown', self.CONTROLLER_NAME, self._name, str(uid), str(gid))
        await proc.communicate()

    async def chmod(self, mod: int) -> None:
        # TODO: validation of `mod`
        proc = await asyncio.create_subprocess_exec('cgm', 'chmod', self.CONTROLLER_NAME, self._name, str(mod))
        await proc.communicate()

    async def chmodfile(self, mod: int) -> None:
        # TODO: validation of `mod`
        proc = await asyncio.create_subprocess_exec('cgm', 'chmodfile', self.CONTROLLER_NAME, self._name, str(mod))
        await proc.communicate()

    @property
    def name(self) -> str:
        return self._name

    async def set_name(self, new_name: str) -> None:
        proc = await asyncio.create_subprocess_exec(
                'sudo', 'mv', str(self.absolute_path() / self._name), str(self.absolute_path() / new_name)
        )
        await proc.communicate()

        self._name = new_name

    async def add_tasks(self, pids: Iterable[int]) -> None:
        proc = await asyncio.create_subprocess_exec('cgclassify', '-g', self.identifier, '--sticky', *map(str, pids))
        await proc.communicate()

    async def delete(self) -> None:
        proc = await asyncio.create_subprocess_exec('sudo', 'cgdelete', '-r', '-g', self.identifier)
        await proc.communicate()
