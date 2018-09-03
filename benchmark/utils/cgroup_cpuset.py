# coding: UTF-8

import subprocess
import asyncio
import shlex
import logging
import getpass
from typing import Set, Dict, List, Tuple, Coroutine, Optional

import psutil


class CgroupCpuset:
    MOUNT_POINT = '/sys/fs/cgroup/cpuset'

    @staticmethod
    def create_group(name: str) -> None:
        subprocess.check_call(args=('sudo', 'mkdir', '-p', f'{CgroupCpuset.MOUNT_POINT}/{name}'))

    @staticmethod
    async def async_create_group(name: str) -> None:
        return await asyncio.create_subprocess_exec('sudo', 'mkdir', '-p', f'{CgroupCpuset.MOUNT_POINT}/{name}')

    @staticmethod
    async def async_chown_group(name: str) -> None:
        return await asyncio.create_subprocess_exec('sudo', 'chown', '-R', f'{getpass.getuser()}',f'{CgroupCpuset.MOUNT_POINT}/{name}')

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
                                                        stdin=asyncio.subprocess.PIPE, check=True, encoding='ASCII',
                                                        stdout=asyncio.subprocess.DEVNULL)
            input_tid = f'{thread.id}\n'.encode()
            await proc.communicate(input_tid)

        for child in p.children(True):
            for thread in child.threads():
                proc = await asyncio.create_subprocess_exec('sudo', 'tee', '-a',
                                                            f'{CgroupCpuset.MOUNT_POINT}/{name}/tasks',
                                                            stdin=asyncio.subprocess.PIPE,
                                                            stdout=asyncio.subprocess.DEVNULL)
                input_tid = f'{thread.id}\n'.encode()
                await proc.communicate(input_tid)

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
        input_core_set = ','.join(map(str, core_set)).encode()
        return await proc.communicate(input_core_set)

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
        input_mem_set = ','.join(map(str, mem_set)).encode()
        return await proc.communicate(input_mem_set)

    @staticmethod
    def cgexec(group_name: str, cmd: str) -> subprocess.CompletedProcess:
        #This function executes the program in a cgroup by using cgexec
        #TODO: Test
        proc = subprocess.run(args=('cgexec', '-g', f'cpuset:{group_name}', *shlex.split(cmd)),
                       check=True, encoding='ASCII', stdout=subprocess.DEVNULL)
        return proc

    @staticmethod
    async def async_cgexec(group_name: str, exec_cmd: str, exec_env: Optional[Dict[str, str]]) -> asyncio.subprocess.Process:
        #This function executes the program in a cgroup by using cgexec
        return await asyncio.create_subprocess_exec('cgexec', '-g', f'cpuset:{group_name}',
                                                    *shlex.split(exec_cmd),
                                                    stdout=asyncio.subprocess.DEVNULL,
                                                    env=exec_env)

    @staticmethod
    async def async_rename_group(group_path: str, new_group_path: str) -> None:
        await asyncio.create_subprocess_exec('sudo', 'mv', f'{group_path}', f'{new_group_path}',
                                                    stdout=asyncio.subprocess.DEVNULL)

    # Below functions are exposed to be used with other framework

    @staticmethod
    async def create_cgroup_cpuset(wl_name: str, identifier: str) -> str:
        group_name = f'{wl_name}_{identifier}'
        await CgroupCpuset.async_create_group(group_name)
        await CgroupCpuset.async_chown_group(group_name)
        return group_name

    @staticmethod
    async def set_cgroup_cpuset(group_name: str,
                                binding_cores: str,
                                host_numa_info: Tuple[Dict[int, List[int]], List[int]]) -> None:
        cpu_topo, _ = host_numa_info
        core_set = CgroupCpuset.convert_to_set(binding_cores)
        await CgroupCpuset.async_assign(group_name, core_set)

    @staticmethod
    async def set_numa_mem_nodes(group_name: str,
                                 binding_cores: str,
                                 numa_mem_nodes: str,
                                 host_numa_info: [Tuple[Dict[int, List[int]], List[int]]]) -> None:
        workload_mem_nodes = set()

        if numa_mem_nodes is None:
            # Local Alloc Case
            cpu_topo, mem_topo = host_numa_info
            for numa_node, cpuid_range in cpu_topo.items():
                min_cpuid, max_cpuid = cpuid_range
                if min_cpuid <= binding_cores <= max_cpuid:
                    if numa_node in mem_topo:
                        workload_mem_nodes.add(numa_node)
        elif numa_mem_nodes is not None:
            # Explicit Mem Node Alloc
            mem_nodes = numa_mem_nodes.split(',')
            workload_mem_nodes = set([int(mem_node) for mem_node in mem_nodes])

        await CgroupCpuset.async_set_cpuset_mems(group_name, workload_mem_nodes)

    @staticmethod
    async def rename_group(group_name: str, wl_name: str, wl_pid: int) -> str:
        base_path: str = CgroupCpuset.MOUNT_POINT
        group_path = f'{base_path}/{group_name}'

        # Create new group name
        new_group_name = f'{wl_name}_{wl_pid}'
        new_group_path = f'{base_path}/{new_group_name}'

        # Rename group name
        await CgroupCpuset.async_rename_group(group_path, new_group_path)
        return new_group_name

    @staticmethod
    def async_exec_cmd(group_name: str, exec_cmd: str, exec_env: Optional[Dict[str, str]]) -> Coroutine:
        return CgroupCpuset.async_cgexec(group_name, exec_cmd, exec_env)
