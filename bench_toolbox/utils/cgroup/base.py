# coding: UTF-8

import getpass
import grp
import os
from abc import ABCMeta
from pathlib import Path
from typing import ClassVar, Iterable

from ..asyncio_subprocess import check_run


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

        await check_run('sudo', 'cgcreate', '-a', f'{uname}:{gname}', '-d', '755', '-f',
                        '644', '-t', f'{uname}:{gname}', '-s', '644', '-g', self.identifier)

    async def chown(self, uid: int, gid: int) -> None:
        await check_run('cgm', 'chown', self.CONTROLLER_NAME, self._name, str(uid), str(gid))

    async def chmod(self, mod: int) -> None:
        # TODO: validation of `mod`
        await check_run('cgm', 'chmod', self.CONTROLLER_NAME, self._name, str(mod))

    async def chmodfile(self, mod: int) -> None:
        # TODO: validation of `mod`
        await check_run('cgm', 'chmodfile', self.CONTROLLER_NAME, self._name, str(mod))

    @property
    def name(self) -> str:
        return self._name

    async def rename(self, new_name: str) -> None:
        if self._name == new_name:
            raise ValueError(f'trying to rename with same cgroup name ({new_name})')

        await check_run('sudo', 'mv', str(self.absolute_path() / self._name), str(self.absolute_path() / new_name))

        self._name = new_name

    async def add_tasks(self, pids: Iterable[int]) -> None:
        await check_run('sudo', 'cgclassify', '-g', self.identifier, '--sticky', *map(str, pids))

    async def delete(self) -> None:
        await check_run('sudo', 'cgdelete', '-r', '-g', self.identifier)
