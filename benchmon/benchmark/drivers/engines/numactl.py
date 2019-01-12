# coding: UTF-8

import asyncio

from .base import BaseEngine
from ...constraints.cgroup import CpusetConstraint


class NumaCtlEngine(BaseEngine):
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
