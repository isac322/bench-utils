# coding: UTF-8

import asyncio
from itertools import chain
from typing import Iterable

from .base import BaseEngine
from ...constraints.cgroup.base import BaseCgroupConstraint


class CGroupEngine(BaseEngine):
    """
    프로그램을 처음 실행할때부터 특정 `cgroup` 의 그룹들에서 실행할 수 있게하는 `cgexec` 을 사용하여 벤치마크를 실행한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`bench_toolbox.benchmark.drivers.engines` 모듈
    """

    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        cgroup_cons: Iterable[BaseCgroupConstraint] = filter(
                lambda x: isinstance(x, BaseCgroupConstraint),
                self._benchmark._constraints
        )

        cgroups = chain(*(('-g', group.identifier) for group in cgroup_cons))

        return await asyncio.create_subprocess_exec('cgexec', *cgroups, *cmd, **kwargs)
