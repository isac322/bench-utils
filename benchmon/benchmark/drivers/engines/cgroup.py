# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABC
from typing import Optional, Type

from .base import BaseEngine
from ...constraints import CGroupConstraint
from .... import Context
from ....benchmark.base import BaseBenchmark
from ....utils.privilege import drop_privilege


class CGroupEngine(BaseEngine, ABC):
    """
    :meth:`~asyncio.create_subprocess_exec` 를 사용하여 벤치마크를 실행한다.

    벤치마크에 `cgroup` 이 설정되어 있을 경우, `preexec_fn` 를 사용하여 실행전에 벤치마크 프로세스를 해당 그룹에 추가한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    @classmethod
    def of(cls, context: Context) -> Optional[Type[CGroupEngine]]:
        # noinspection PyProtectedMember
        return context._variable_dict.get(cls)

    @classmethod
    async def launch(cls, context: Context, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        benchmark = BaseBenchmark.of(context)

        for constraint in benchmark._constraints:
            if isinstance(constraint, CGroupConstraint):
                kwargs['preexec_fn'] = constraint.cgroup.add_current_process
                break

        from ....configs.containers import PrivilegeConfig
        privilege_config = PrivilegeConfig.of(context).execute

        with drop_privilege(privilege_config.user, privilege_config.group):
            return await asyncio.create_subprocess_exec(*cmd, **kwargs)
