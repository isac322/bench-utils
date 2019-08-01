# coding: UTF-8

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple, Type, TypeVar

from .base import BaseConfig

if TYPE_CHECKING:
    from pathlib import Path

    from ..containers import PrivilegeConfig
    from ...benchmark import BaseBenchmark, BaseBuilder
    from ...benchmark.constraints import BaseConstraint

    _BT = TypeVar('_BT', bound=BaseBenchmark)
    _CST_T = TypeVar('_CST_T', bound=BaseConstraint)


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    __slots__ = (
        '_bench_class', 'num_of_threads', 'type', '_init_constraints', 'identifier', 'workspace', 'width_in_log'
    )

    _bench_class: Type[_BT]
    num_of_threads: int
    type: str
    _init_constraints: Tuple[_CST_T, ...]
    identifier: str
    workspace: Path
    width_in_log: int

    def generate_builder(self, privilege_config: PrivilegeConfig, logger_level: int = logging.INFO) -> BaseBuilder:
        return self._bench_class.Builder(self, privilege_config, logger_level)


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    __slots__ = ('name',)

    name: str


@dataclass(frozen=True)
class SSHConfig(BenchConfig):
    __slots__ = ('host', 'command', 'port', 'tunnel', 'local_addr', 'options')

    host: str
    command: str
    port: Optional[int]
    tunnel: Optional[Dict[str, Any]]
    local_addr: Optional[Tuple[str, int]]
    options: Optional[Dict[str, Any]]
