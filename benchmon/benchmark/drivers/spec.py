# coding: UTF-8

import asyncio
import os
import shlex
from signal import SIGCONT, SIGSTOP
from typing import ClassVar, FrozenSet, Optional

import psutil

from .base import BenchDriver
from .engines.base import BaseEngine
from ... import Context


class SpecDriver(BenchDriver):
    """ SPEC CPU 벤치마크의 실행을 담당하는 드라이버 """

    _benches: ClassVar[FrozenSet[str]] = frozenset((
        'lbm', 'libquantum', 'GemsFDTD', 'sphinx', 'gcc', 'zeusmp', 'sjeng'
    ))
    bench_name: ClassVar[str] = 'spec'

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'sphinx':
            exec_name = 'sphinx_livepretend_base.proc'
        else:
            exec_name = f'{self._name}_base.proc'

        for process in self._wrapper_proc_info.children(recursive=True):
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self, context: Context) -> asyncio.subprocess.Process:
        cmd = f'runspec --config=vm.cfg --size=ref --noreportable --delay=0 --nobuild --iteration=1 {self._name}'

        bench_bin = os.path.join(SpecDriver._bench_home, 'bin')
        bench_lib = os.path.join(bench_bin, 'lib')

        env = os.environ.copy()
        env['PATH'] = bench_bin + ':' + env['PATH']
        env['SPEC'] = SpecDriver._bench_home
        env['SPECPERLLIB'] = f'{bench_bin}:{bench_lib}'
        env['LC_LANG'] = 'C'
        env['LC_ALL'] = 'C'

        engine = BaseEngine.of(context)

        return await engine.launch(context, *shlex.split(cmd), stdout=asyncio.subprocess.DEVNULL, env=env)

    def stop(self) -> None:
        try:
            proc = self._find_bench_proc()
            if proc is not None:
                proc.kill()
        except psutil.NoSuchProcess:
            pass

        super().stop()

    def pause(self) -> None:
        self._wrapper_proc.send_signal(SIGSTOP)
        self._find_bench_proc().suspend()

    def resume(self) -> None:
        self._wrapper_proc.send_signal(SIGCONT)
        self._find_bench_proc().resume()
