# coding: UTF-8

import asyncio
from itertools import chain
from typing import Iterable

from .base import BaseEngine
from ...constraints.cgroup.base import BaseCgroupConstraint


class CGroupEngine(BaseEngine):
    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        cgroup_cons: Iterable[BaseCgroupConstraint] = filter(
                lambda x: isinstance(x, BaseCgroupConstraint),
                self._benchmark._constraints
        )

        cgroups = chain(*(('-g', group.identifier) for group in cgroup_cons))

        return await asyncio.create_subprocess_exec('cgexec', '--sticky', *cgroups, *cmd, **kwargs)
