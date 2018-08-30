# coding: UTF-8

import subprocess
import asyncio
import shlex
from typing import Set

import psutil


class CgroupCpuset:
    MOUNT_POINT = '/sys/fs/cgroup/cpuset'

    @staticmethod
    def create_group(name: str) -> None:
        subprocess.check_call(args=('sudo', 'mkdir', '-p', f'{CgroupCpuset.MOUNT_POINT}/{name}'))

    @staticmethod
    async def async_create_group(name: str) -> None:
        await asyncio.create_subprocess_exec('sudo', 'mkdir', '-p', f'{CgroupCpuset.MOUNT_POINT}/{name}')

    @staticmethod
    def add_task(name: str, pid: int) -> None:
        p = psutil.Process(pid)

        for thread in p.threads():
            subprocess.run(args=('sudo', 'tee', '-a', f'{CgroupCpuset.MOUNT_POINT}/{name}/tasks'),
                           input=f'{thread.id}\n', check=True, encoding='ASCII', stdout=subprocess.DEVNULL)

        for child in p.children(True):
            for thread in child.threads():
                subprocess.run(args=('sudo', 'tee', '-a', f'{CgroupCpuset.MOUNT_POINT}/{name}/tasks'),
                               input=f'{thread.id}\n', check=True, encoding='ASCII', stdout=subprocess.DEVNULL)

    @staticmethod
    async def async_add_task(name: str, pid: int) -> None:
        p = psutil.Process(pid)

        for thread in p.threads():
            proc = await asyncio.create_subprocess_exec('sudo', 'tee', '-a', f'{CgroupCpuset.MOUNT_POINT}/{name}/tasks',
                           stdin=asyncio.subprocess.PIPE, check=True, encoding='ASCII', stdout=asyncio.subprocess.DEVNULL)
            await proc.communicate(f'{thread.id}\n')

        for child in p.children(True):
            for thread in child.threads():
                proc = await asyncio.create_subprocess_exec('sudo', 'tee', '-a', f'{CgroupCpuset.MOUNT_POINT}/{name}/tasks',
                               stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)
                await proc.communicate(f'{thread.id}\n')

    @staticmethod
    def remove_group(name: str) -> None:
        subprocess.check_call(args=('sudo', 'rmdir', f'/sys/fs/cgroup/cpuset/{name}'))

    @staticmethod
    async def async_remove_group(name: str) -> None:
        await asyncio.create_subprocess_exec('sudo', 'rmdir', f'/sys/fs/cgroup/cpuset/{name}')

    @staticmethod
    def assign(group_name: str, core_set: Set[int]) -> None:
        subprocess.run(args=('sudo', 'tee', f'/sys/fs/cgroup/cpuset/{group_name}/cpuset.cpus'),
                       input=','.join(map(str, core_set)), check=True, encoding='ASCII', stdout=subprocess.DEVNULL)

    @staticmethod
    async def async_assign(group_name: str, core_set: Set[int]) -> None:
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', f'/sys/fs/cgroup/cpuset/{group_name}/cpuset.cpus',
                       stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)
        input_core_set = ','.join(map(str, core_set))
        await proc.communicate(f'{input_core_set}')

    @staticmethod
    def convert_to_set(hyphen_str: str) -> Set[int]:
        ret = set()

        for elem in hyphen_str.split(','):
            group = tuple(map(int, elem.split('-')))

            if len(group) is 1:
                ret.add(group[0])
            elif len(group) is 2:
                ret.update(range(group[0], group[1] + 1))

        return ret

    @staticmethod
    def set_cpuset_mems(group_name: str, mem_set: Set[int]) -> None:
        subprocess.run(args=('sudo', 'tee', f'/sys/fs/cgroup/cpuset/{group_name}/cpuset.mems'),
                       input=','.join(map(str, mem_set)), check=True, encoding='ASCII', stdout=subprocess.DEVNULL)

    @staticmethod
    async def async_set_cpuset_mems(group_name: str, mem_set: Set[int]) -> None:
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', f'/sys/fs/cgroup/cpuset/{group_name}/cpuset.mems',
                       stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)
        input_mem_set = ','.join(map(str, mem_set))
        await proc.communicate(f'{input_mem_set}')

    @staticmethod
    def cgexec(group_name: str, cmd: str) -> None:
        # This function executes the program in a cgroup by using cgexec
        subprocess.run(args=('sudo', 'cgexec', '-g', f'cpuset:{group_name}', *shlex.split(cmd)),
                       check=True, encoding='ASCII', stdout=subprocess.DEVNULL)

    @staticmethod
    async def async_cgexec(group_name: str, cmd: str) -> None:
        #This function executes the program in a cgroup by using cgexec
        await asyncio.create_subprocess_exec('sudo', 'cgexec', '-g', f'cpuset:{group_name}',
                                             *shlex.split(cmd),
                                             stdout=asyncio.subprocess.DEVNULL)
