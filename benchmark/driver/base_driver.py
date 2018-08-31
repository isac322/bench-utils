# coding: UTF-8

import asyncio
import aiofiles
import json
from itertools import chain
from signal import SIGCONT, SIGSTOP
from typing import Any, Callable, Iterable, Optional, Set, Type, Tuple, List, Dict, Coroutine
from pathlib import Path
from ..utils.cgroup_cpuset import CgroupCpuset

import functools
import psutil
from abc import ABCMeta, abstractmethod


class BenchDriver(metaclass=ABCMeta):
    class _Decorators:
        @staticmethod
        def ensure_running(func: Callable[['BenchDriver', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'BenchDriver', *args, **kwargs):
                if not self.is_running:
                    raise RuntimeError(f'The benchmark ({self._name}) has already ended or never been invoked.'
                                       ' Run benchmark first via invoking `run()`!')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_not_running(func: Callable[['BenchDriver', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'BenchDriver', *args, **kwargs):
                if self.is_running:
                    raise RuntimeError(f'The benchmark ({self._name}) has already ended or never been invoked.'
                                       ' Run benchmark first via invoking `run()`!')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_invoked(func: Callable[['BenchDriver', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'BenchDriver', *args, **kwargs):
                if not self.has_invoked:
                    raise RuntimeError(f'The benchmark ({self._name}) has never been invoked.'
                                       ' Run benchmark first via invoking `run()`!')
                return func(self, *args, **kwargs)

            return decorator

    _benches: Set[str] = None
    _bench_home: str = None
    bench_name: str = None

    def __init__(self, name: str, identifier: str, num_threads: int, binding_cores: str, numa_mem_nodes: Optional[str]):
        self._name: str = name
        self._identifier: str = identifier
        self._num_threads: int = num_threads
        self._binding_cores: str = binding_cores
        self._numa_mem_nodes: Optional[str] = numa_mem_nodes

        self._host_numa_info: Optional[Tuple[Dict[int, List[int], List[int]]]] = None
        self._bench_proc_info: Optional[psutil.Process] = None
        self._async_proc: Optional[asyncio.subprocess.Process] = None
        self._async_proc_info: Optional[psutil.Process] = None
        self._group_name: str = None

    def __del__(self):
        try:
            self.stop()
        except (psutil.NoSuchProcess, ProcessLookupError):
            pass

    @staticmethod
    @abstractmethod
    def has(bench_name: str) -> bool:
        pass

    @staticmethod
    def get_bench_home(bench_name: str) -> str:
        from benchmark_launcher import GLOBAL_CFG_PATH
        with open(GLOBAL_CFG_PATH) as fp:
            return json.load(fp)['benchmark'][bench_name]

    @property
    def name(self) -> str:
        return self._name

    @property
    @_Decorators.ensure_invoked
    def created_time(self) -> float:
        return self._bench_proc_info.create_time()

    @property
    def _is_running(self) -> bool:
        """
        Check if this benchmark is running.

        The difference with :func:`benchmark.driver.base_driver.BenchDriver.is_running` is this method is more precise,
        but has more cost.

        :return: True if running
        """
        return self.is_running and self._find_bench_proc() is not None

    @property
    def has_invoked(self):
        return self._bench_proc_info is not None and \
               self._async_proc is not None and \
               self._async_proc_info is not None

    @property
    def is_running(self):
        return self.has_invoked and self._bench_proc_info.is_running()

    @property
    def pid(self) -> Optional[int]:
        """
        Get effective pid of this benchmark (not python pid) without blocking.
        :return: actual pid of benchmark process
        """
        if self._bench_proc_info is None:
            return None
        else:
            return self._bench_proc_info.pid

    @abstractmethod
    async def _launch_bench(self) -> asyncio.subprocess.Process:
        pass

    @abstractmethod
    def _find_bench_proc(self) -> Optional[psutil.Process]:
        pass

    @_Decorators.ensure_not_running
    async def run(self) -> None:
        self._bench_proc_info = None
        self._host_numa_info = await self.get_numa_info()
        self._async_proc = await self._launch_bench()
        self._async_proc_info = psutil.Process(self._async_proc.pid)
        self.rename_group(self._async_proc)

        while True:
            self._bench_proc_info = self._find_bench_proc()
            if self._bench_proc_info is not None:
                return
            await asyncio.sleep(0.1)

    @_Decorators.ensure_running
    async def join(self) -> None:
        await self._async_proc.wait()

    def stop(self) -> None:
        self._async_proc.kill()
        self._bench_proc_info.kill()
        self._async_proc_info.kill()

    @_Decorators.ensure_running
    def pause(self) -> None:
        self._async_proc.send_signal(SIGSTOP)
        self._bench_proc_info.suspend()

    @_Decorators.ensure_running
    def resume(self) -> None:
        self._async_proc.send_signal(SIGCONT)
        self._bench_proc_info.resume()

    @_Decorators.ensure_running
    def all_child_tid(self) -> Iterable[int]:
        return chain(
                (t.id for t in self._bench_proc_info.threads()),
                *((t.id for t in proc.threads()) for proc in self._bench_proc_info.children(recursive=True))
        )

    @_Decorators.ensure_not_running
    async def _get_node_topo(self, _base_path: str) -> List[int]:
        base_path = Path(_base_path)
        online_path = base_path / 'online'
        async with aiofiles.open(online_path) as fp:
            line: str = fp.readline()
            node_list = [int(num) for num in line.split('-')]
        return node_list

    @_Decorators.ensure_not_running
    async def _get_cpu_topo(self, _base_path: str, node_list: List[int]) -> Dict[int, List[List[int]]]:
        base_path = Path(_base_path)
        cpu_topo: Dict[int, List[List[int]]] = dict()

        for num in node_list:
            cpulist_path = base_path / f'node{num}/cpulist'

            async with aiofiles.open(cpulist_path) as fp:
                line: str = fp.readline()
                cpu_ranges: List[List[str]] = [cpus.split('-') for cpus in line.split(',')]
                int_cpu_ranges: List[List[int]] = list()
                for cpu_range in cpu_ranges:
                    int_cpu_range = [int(cpuid) for cpuid in cpu_range]
                    int_cpu_ranges.append(int_cpu_range)
                cpu_topo[num] = int_cpu_ranges
        return cpu_topo

    @_Decorators.ensure_not_running
    async def _get_mem_topo(self, _base_path: str) -> List[int]:
        base_path = Path(_base_path)
        has_memory_path = base_path / 'has_memory'

        async with aiofiles.open(has_memory_path) as fp:
            line: str = fp.readline()
            mem_list = line.split('-')
            mem_topo = [int(num) for num in mem_list]

            # TODO: mem_topo can be enhanced by using real numa memory access latency

        return mem_topo

    @_Decorators.ensure_not_running
    async def get_numa_info(self) -> Tuple[Dict[int, List[List[int]]], List[int]]:
        _base_path = '/sys/devices/system/node'

        node_list = await self._get_node_topo(self, _base_path)
        cpu_topo = await self._get_cpu_topo(self, _base_path, node_list)
        mem_topo = await self._get_mem_topo(self, _base_path)
        return cpu_topo, mem_topo

    @_Decorators.ensure_not_running
    async def create_cgroup_cpuset(self) -> None:
        self._group_name = f'{self._async_proc.name()}_{self._identifier}'
        CgroupCpuset.async_create_group(self._group_name)

    @_Decorators.ensure_not_running
    async def set_cgroup_cpuset(self) -> None:
        cpu_topo, _ = self._host_numa_info
        core_set = CgroupCpuset.convert_to_set(self._binding_cores)
        CgroupCpuset.async_assign(self._group_name, core_set)

    @_Decorators.ensure_not_running
    async def set_numa_mem_nodes(self) -> None:
        workload_mem_nodes = set()

        if self._numa_mem_nodes is None:
            # Local Alloc Case
            cpu_topo, mem_topo = self._host_numa_info
            for numa_node, cpuid_range in cpu_topo.items():
                min_cpuid, max_cpuid = cpuid_range
                if min_cpuid <= self._binding_cores <= max_cpuid:
                    if numa_node in mem_topo:
                        workload_mem_nodes.add(numa_node)
        elif self._numa_mem_nodes is not None:
            # Explicit Mem Node Alloc
            mem_nodes = self._numa_mem_nodes.split(',')
            workload_mem_nodes = set([int(mem_node) for mem_node in mem_nodes])

        CgroupCpuset.async_set_cpuset_mems(self._group_name, workload_mem_nodes)

    @_Decorators.ensure_not_running
    def async_exec_cmd(self, exec_cmd: str) -> Coroutine:
        return CgroupCpuset.async_cgexec(self._group_name, exec_cmd)

    @_Decorators.ensure_running
    async def rename_group(self) -> None:
        base_path: str = CgroupCpuset.MOUNT_POINT
        group_path = f'{base_path}/{self._group_name}'

        # Create new group name
        new_group_name = f'{self._async_proc_info.name()}_{self._async_proc.pid}'
        new_group_path = f'{base_path}/{new_group_name}'

        # Rename group name
        CgroupCpuset.async_rename_group(group_path, new_group_path)
        self._group_name = new_group_name



def find_driver(workload_name) -> Type[BenchDriver]:
    from benchmark.driver.spec_driver import SpecDriver
    from benchmark.driver.parsec_driver import ParsecDriver
    from benchmark.driver.rodinia_driver import RodiniaDriver
    from benchmark.driver.npb_driver import NPBDriver

    bench_drivers = (SpecDriver, ParsecDriver, RodiniaDriver, NPBDriver)

    for _bench_driver in bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def bench_driver(workload_name: str, identifier: str, num_threads: int, binding_cores: str, numa_mem_nodes: Optional[str]) -> BenchDriver:
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, identifier, num_threads, binding_cores, numa_mem_nodes)
