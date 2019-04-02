# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .base import BaseEngine
from ...constraints import CGroupConstraint
from ....utils.privilege import drop_privilege

if TYPE_CHECKING:
    from .... import Context


class NumaCtlEngine(BaseEngine):
    """
    프로그램을 처음 실행할때부터 메모리나 CPU 사용을 제한할 수 있게하는 `numactl` 을 사용하여 벤치마크를 실행한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    @classmethod
    async def launch(cls, context: Context, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        from ....configs.containers import PrivilegeConfig
        privilege_config = PrivilegeConfig.of(context).execute

        constraint = CGroupConstraint.of(context)

        if constraint is not None:
            initial_values = constraint.initial_values()

            if 'cpuset.mems' is initial_values:
                mem_flag = '--localalloc'
            else:
                mem_flag = '--membind={}'.format(initial_values['cpuset.mems'])

            if 'cpuset.cpus' is initial_values:
                cpu_flag = ''
            else:
                cpu_flag = '--physcpubind={}'.format(initial_values['cpuset.cpus'])

            with drop_privilege(privilege_config.user, privilege_config.group):
                return await asyncio.create_subprocess_exec(
                        'numactl',
                        cpu_flag,
                        mem_flag,
                        *cmd, **kwargs)

        with drop_privilege(privilege_config.user, privilege_config.group):
            return await asyncio.create_subprocess_exec(*cmd, **kwargs)
