# coding: UTF-8

import asyncio
import shlex
from typing import ClassVar, FrozenSet, Optional

import psutil

from .base import BenchDriver
from .engines.base import BaseEngine
from ... import Context
from ...benchmark import BaseBenchmark


class ParsecDriver(BenchDriver):
    """ PARSEC 벤치마크의 실행을 담당하는 드라이버 """

    _benches: ClassVar[FrozenSet[str]] = frozenset((
        'streamcluster', 'canneal', 'swaptions', 'x264', 'ferret', 'bodytrack', 'blackscholes',
        'dedup', 'facesim', 'fluidanimate', 'freqmine', 'raytrace', 'vips'
    ))
    bench_name: ClassVar[str] = 'parsec'

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'raytrace':
            exec_name = 'rtview'
        else:
            exec_name = self._name

        for process in self._wrapper_proc_info.children(recursive=True):
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self, context: Context) -> asyncio.subprocess.Process:
        engine = BaseEngine.of(context)
        config = BaseBenchmark.of(context).bench_config

        cmd = f'{self._bench_home}/parsecmgmt -a run -p {self._name} -i native -n {config.num_of_threads}'

        return await engine.launch(context, *shlex.split(cmd), stdout=asyncio.subprocess.DEVNULL)
