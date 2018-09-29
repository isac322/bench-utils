# coding: UTF-8

import asyncio
import os
import shlex
from signal import SIGCONT, SIGSTOP
from typing import ClassVar, Optional, Set

import psutil

from .base import BenchDriver
from ..decorators.driver import ensure_running


class SpecDriver(BenchDriver):
    _benches: ClassVar[Set[str]] = {'lbm', 'libquantum', 'GemsFDTD', 'sphinx', 'gcc', 'zeusmp', 'sjeng'}
    bench_name: ClassVar[str] = 'spec'

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in SpecDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'sphinx':
            exec_name = 'sphinx_livepretend_base.proc'
        else:
            exec_name = f'{self._name}_base.proc'

        for process in self._wrapper_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        cmd = f'runspec --config=vm.cfg --size=ref --noreportable --delay=0 --nobuild --iteration=1 {self._name}'

        bench_bin = os.path.join(SpecDriver._bench_home, 'bin')
        bench_lib = os.path.join(bench_bin, 'lib')

        env = os.environ.copy()
        env['PATH'] = bench_bin + ':' + env['PATH']
        env['SPEC'] = SpecDriver._bench_home
        env['SPECPERLLIB'] = f'{bench_bin}:{bench_lib}'
        env['LC_LANG'] = 'C'
        env['LC_ALL'] = 'C'

        return await self._engine.launch(*shlex.split(cmd), stdout=asyncio.subprocess.DEVNULL, env=env)

    def stop(self) -> None:
        try:
            proc = self._find_bench_proc()
            if proc is not None:
                proc.kill()
        except psutil.NoSuchProcess:
            pass

        super().stop()

    @ensure_running
    def pause(self) -> None:
        self._wrapper_proc.send_signal(SIGSTOP)
        self._find_bench_proc().suspend()

    @ensure_running
    def resume(self) -> None:
        self._wrapper_proc.send_signal(SIGCONT)
        self._find_bench_proc().resume()
