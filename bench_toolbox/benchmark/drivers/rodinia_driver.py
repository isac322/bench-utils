# coding: UTF-8

import asyncio
import shlex
from typing import Optional, Set

import psutil

from .base_driver import BenchDriver


class RodiniaDriver(BenchDriver):
    _benches: Set[str] = {'nn', 'kmeans', 'cfd', 'particlefilter', 'bfs'}
    bench_name: str = 'rodinia'

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in RodiniaDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'cfd':
            exec_name = 'euler3d_cpu'
        elif self._name == 'particlefilter':
            exec_name = 'particle_filter'
        else:
            exec_name = self._name

        for process in self._async_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        if self._numa_cores is None:
            mem_flag = '--localalloc'
        else:
            mem_flag = f'--membind={self._numa_cores}'

        cmd = '--physcpubind={0} {1} {2}/openmp/{3}/run' \
            .format(self._binging_cores, mem_flag, self._bench_home, self._name)

        return await asyncio.create_subprocess_exec(
                'numactl',
                *shlex.split(cmd),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env={
                    'OMP_NUM_THREADS': str(self._num_threads),
                    'GOMP_CPU_AFFINITY': str(self._binging_cores)
                })
