# coding: UTF-8

import asyncio

from .base import BaseEngine
from ...constraints import CGroupConstraint


class CGroupEngine(BaseEngine):
    """
    프로그램을 처음 실행할때부터 특정 `cgroup` 의 그룹들에서 실행할 수 있게하는 `cgexec` 을 사용하여 벤치마크를 실행한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        for constraint in self._benchmark._constraints:
            if isinstance(constraint, CGroupConstraint):
                kwargs['preexec_fn'] = constraint.cgroup.add_current_process

        return await asyncio.create_subprocess_exec(*cmd, **kwargs)
