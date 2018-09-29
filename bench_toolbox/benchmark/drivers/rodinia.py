# coding: UTF-8

import asyncio
from typing import ClassVar, Optional, Set

import psutil

from .base import BenchDriver


class RodiniaDriver(BenchDriver):
    _benches: ClassVar[Set[str]] = {'nn', 'kmeans', 'cfd', 'particlefilter', 'bfs'}
    bench_name: ClassVar[str] = 'rodinia'

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

        for process in self._wrapper_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        return await self._engine.launch(
                f'{self._bench_home}/openmp/{self._name}/run',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env={'OMP_NUM_THREADS': str(self._num_threads)})
