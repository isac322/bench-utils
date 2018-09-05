# coding: UTF-8

import asyncio
import getpass
import grp
import os
import shlex
from typing import Iterable


class CgroupCpuset:
    MOUNT_POINT = '/sys/fs/cgroup/cpuset'

    def __init__(self, group_name: str) -> None:
        self._group_name: str = group_name
        self._group_path: str = f'cpuset:{group_name}'

    async def create_group(self) -> None:
        uname: str = getpass.getuser()
        gid: int = os.getegid()
        gname: str = grp.getgrgid(gid).gr_name

        proc = await asyncio.create_subprocess_exec(
                'sudo', 'cgcreate', '-a', f'{uname}:{gname}', '-d', '700', '-f',
                '600', '-t', f'{uname}:{gname}', '-s', '600', '-g', self._group_path)
        await proc.communicate()

    async def exec_command(self, command: str, **kwargs) -> asyncio.subprocess.Process:
        return await asyncio.create_subprocess_exec(
                'cgexec', '--sticky', '-g', self._group_path, *shlex.split(command), **kwargs)

    async def rename(self, new_group_name) -> None:
        proc = await asyncio.create_subprocess_exec(
                'sudo', 'mv', f'{CgroupCpuset.MOUNT_POINT}/{self._group_name}',
                f'{CgroupCpuset.MOUNT_POINT}/{new_group_name}'
        )
        await proc.communicate()

        self._group_name = new_group_name
        self._group_path = f'cpuset:{self._group_name}'

    async def assign_cpus(self, core_ids: str) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpuset.cpus={core_ids}', self._group_name)
        await proc.communicate()

    async def assign_mems(self, socket_ids: str) -> None:
        proc = await asyncio.create_subprocess_exec('cgset', '-r', f'cpuset.mems={socket_ids}', self._group_name)
        await proc.communicate()

    async def add_tasks(self, pids: Iterable[int]) -> None:
        proc = await asyncio.create_subprocess_exec('cgclassify', '-g', self._group_path, '--sticky', *map(str, pids))
        await proc.communicate()

    async def delete(self) -> None:
        proc = await asyncio.create_subprocess_exec('sudo', 'cgdelete', '-r', '-g', self._group_path)
        await proc.communicate()
