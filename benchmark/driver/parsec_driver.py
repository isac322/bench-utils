# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver
import logging


class ParsecDriver(BenchDriver):
    _benches: Set[str] = {'streamcluster', 'canneal', 'swaptions', 'x264', 'ferret', 'bodytrack', 'blackscholes',
                          'dedup', 'facesim', 'fluidanimate', 'freqmine', 'raytrace', 'vips'}
    bench_name: str = 'parsec'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in ParsecDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'raytrace':
            exec_name = 'rtview'
        else:
            exec_name = self._name

        for process in self._async_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        await self.create_cgroup_cpuset()
        await self.set_cgroup_cpuset()
        await self.set_numa_mem_nodes()
        cmd = '{0}/parsecmgmt -a run -p {1} -i native -n {2}' \
            .format(self._bench_home, self._name, self._num_threads)

        return await self.async_exec_cmd(exec_cmd=cmd)
        #return await asyncio.create_subprocess_exec(*shlex.split(cmd), stdout=asyncio.subprocess.DEVNULL)
