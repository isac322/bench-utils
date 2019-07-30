# coding: UTF-8

from __future__ import annotations

import copy
from itertools import chain
from typing import Mapping, Optional, TYPE_CHECKING, Tuple, Union

from libcgroup import CGroup
from libcgroup_bind.groups import DeleteFlag

from .base import BaseConstraint
from .. import BaseBenchmark
from ...configs.containers import PrivilegeConfig

if TYPE_CHECKING:
    from ... import Context


class CGroupConstraint(BaseConstraint):
    """
    같은 경로를 가지는 여러 서브 시스템의 cgroup들을 묶어서 하나로 관리하는 constraint
    """
    _cgroup: Optional[CGroup] = None
    _identifier: str
    _controllers: Tuple[str, ...]
    _values: Mapping[str, Union[int, bool, str]]

    def __init__(self,
                 identifier: str,
                 first_controller: str,
                 *controllers: str,
                 **values: Union[int, bool, str]) -> None:
        self._identifier = identifier
        self._controllers = tuple(chain((first_controller,), controllers))
        self._values = values

    async def on_init(self, context: Context) -> None:
        privilege = PrivilegeConfig.of(context).cgroup

        self._cgroup = CGroup(self._identifier, *self._controllers,
                              t_uid=privilege.user, a_uid=privilege.user,
                              t_gid=privilege.group, a_gid=privilege.group,
                              auto_delete=True, auto_delete_flag=DeleteFlag.RECURSIVE)

        for key, val in self._values.items():
            self._cgroup.set_value(key, val)

    async def on_start(self, context: Context) -> None:
        self._cgroup.move_to(BaseBenchmark.of(context).group_name)

    async def on_destroy(self, context: Context) -> None:
        if self._cgroup is not None:
            self._cgroup.delete(DeleteFlag.RECURSIVE)

    @property
    def cgroup(self) -> Optional[CGroup]:
        return self._cgroup

    @property
    def identifier(self) -> str:
        """
        이 constraint가 사용하는 cgroup의 group이름을 반환한다

        :return: 그룹이름
        :rtype: str
        """
        if self._cgroup is None:
            return self._identifier
        else:
            return str(self._cgroup.path)

    def initial_values(self) -> Mapping[str, Union[int, bool, str]]:
        return copy.copy(self._values)
