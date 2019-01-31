# coding: UTF-8

import asyncio

from .base import BaseEngine
from ...constraints.cgroup import CpusetConstraint


class NumaCtlEngine(BaseEngine):
    """
    프로그램을 처음 실행할때부터 메모리나 CPU 사용을 제한할 수 있게하는 `numactl` 을 사용하여 벤치마크를 실행한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`bench_toolbox.benchmark.drivers.engines` 모듈
    """

    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        for constraint in self._benchmark._constraints:
            if isinstance(constraint, CpusetConstraint):
                if constraint.mems is None:
                    mem_flag = '--localalloc'
                else:
                    mem_flag = '--membind={}'.format(constraint.mems)

                return await asyncio.create_subprocess_exec(
                        'numactl',
                        '--physcpubind={}'.format(constraint.cpus),
                        mem_flag,
                        *cmd, **kwargs)

        return await asyncio.create_subprocess_exec(*cmd, **kwargs)
