# coding: UTF-8

import asyncio

from .base import BaseEngine
from ...constraints import CGroupConstraint
from .... import Context
from ....utils.privilege import drop_privilege


class CGroupEngine(BaseEngine):
    """
    :meth:`~asyncio.create_subprocess_exec` 를 사용하여 벤치마크를 실행한다.

    벤치마크에 `cgroup` 이 설정되어 있을 경우, `preexec_fn` 를 사용하여 실행전에 벤치마크 프로세스를 해당 그룹에 추가한다.

    .. seealso::

        엔진의 목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    async def launch(self, context: Context, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        for constraint in self._benchmark._constraints:
            if isinstance(constraint, CGroupConstraint):
                kwargs['preexec_fn'] = constraint.cgroup.add_current_process
                break

        from ....configs.containers import PrivilegeConfig
        privilege_config = PrivilegeConfig.of(context).execute

        with drop_privilege(privilege_config.user, privilege_config.group):
            return await asyncio.create_subprocess_exec(*cmd, **kwargs)
