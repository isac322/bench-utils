# coding: UTF-8

import asyncio
import shlex
from typing import ClassVar, Optional, Set

import psutil

from .base_driver import BenchDriver


class ParsecDriver(BenchDriver):
    _benches: ClassVar[Set[str]] = {
        'streamcluster', 'canneal', 'swaptions', 'x264', 'ferret', 'bodytrack', 'blackscholes',
        'dedup', 'facesim', 'fluidanimate', 'freqmine', 'raytrace', 'vips'
    }
    bench_name: ClassVar[str] = 'parsec'

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in ParsecDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'raytrace':
            exec_name = 'rtview'
        else:
            exec_name = self._name

        for process in self._wrapper_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        cmd = f'{self._bench_home}/parsecmgmt -a run -p {self._name} -i native -n {self._num_threads}'

        return await self._engine.launch(*shlex.split(cmd), stdout=asyncio.subprocess.DEVNULL)
