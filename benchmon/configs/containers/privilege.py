# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import BaseConfig
from ... import ContextReadable

if TYPE_CHECKING:
    from ... import Context


@dataclass(frozen=True)
class Privilege:
    __slots__ = ('user', 'group')

    user: int
    group: int


@dataclass(frozen=True)
class PrivilegeConfig(BaseConfig, ContextReadable):
    """
    각 상황별로 프레임워크가 파일을 생성하거나 프로세스를 시작할 때 어떤 권한으로 할 것인지 기록한다.
    예를 들어 벤치마크를 실행하기위해 프로세스를 실행할 때는 `root` 계정으로 실행했다가, 결과 파일을 저장할 때는 `1000` 번 계정으로
    파일을 생성하기 원할 경우, `execute` 의 `user` 에 `root` 를, `result` 의 `user` 에는 `1000` 을 저장함으로써 프레임워크에서
    상황별로 권한을 바꿀 수 있게 한다.
    """
    __slots__ = ('execute', 'monitor', 'cgroup', 'result')

    execute: Privilege
    monitor: Privilege
    cgroup: Privilege
    result: Privilege

    @classmethod
    def of(cls, context: Context) -> PrivilegeConfig:
        # noinspection PyProtectedMember
        return context._variable_dict[cls]
