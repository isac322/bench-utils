# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .base import BaseEngine
from ...constraints import CGroupConstraint
from ....configs.containers import PrivilegeConfig
from ....exceptions import InitRequiredError
from ....utils.privilege import drop_privilege

if TYPE_CHECKING:
    from .... import Context


class CGroupEngine(BaseEngine):
    """
    :meth:`~asyncio.create_subprocess_exec` 를 사용하여 벤치마크를 실행한다.

    벤치마크에 `cgroup` 이 설정되어 있을 경우, `preexec_fn` 를 사용하여 실행전에 벤치마크 프로세스를 해당 그룹에 추가한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    @classmethod
    async def launch(cls, context: Context, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        constraint = CGroupConstraint.of(context)
        if constraint is not None:
            if constraint.cgroup is None:
                raise InitRequiredError(
                        f'Initialize the {type(constraint).__name__} before running the benchmark.'
                )

            kwargs['preexec_fn'] = constraint.cgroup.add_current_process

        privilege_config = PrivilegeConfig.of(context).execute

        with drop_privilege(privilege_config.user, privilege_config.group):
            return await asyncio.create_subprocess_exec(*cmd, **kwargs)
