# coding: UTF-8

import asyncio
from typing import ClassVar, FrozenSet, Optional

import psutil

from .base import BenchDriver
from .engines.base import BaseEngine
from ... import Context
from ...benchmark import BaseBenchmark


class RodiniaDriver(BenchDriver):
    """ Rodinia 벤치마크의 실행을 담당하는 드라이버 """

    _benches: ClassVar[FrozenSet[str]] = frozenset(('nn', 'kmeans', 'cfd', 'particlefilter', 'bfs'))
    bench_name: ClassVar[str] = 'rodinia'

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'cfd':
            exec_name = 'euler3d_cpu'
        elif self._name == 'particlefilter':
            exec_name = 'particle_filter'
        else:
            exec_name = self._name

        for process in self._wrapper_proc_info.children(recursive=True):
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self, context: Context) -> asyncio.subprocess.Process:
        engine = BaseEngine.of(context)
        config = BaseBenchmark.of(context).bench_config

        return await engine.launch(
                context,
                f'{self._bench_home}/openmp/{self._name}/run',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env={'OMP_NUM_THREADS': str(config.num_of_threads)}
        )
