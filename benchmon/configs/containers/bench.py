# coding: UTF-8

from __future__ import annotations

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple, TypeVar

from .base import BaseConfig

if TYPE_CHECKING:
    from pathlib import Path

    from ..containers import PrivilegeConfig
    from ...benchmark import BaseBuilder, LaunchableBenchmark
    from ...benchmark.constraints import BaseConstraint

    _CST_T = TypeVar('_CST_T', bound=BaseConstraint)


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    __slots__ = ('num_of_threads', 'type', '_init_constraints', 'identifier', 'workspace', 'width_in_log')

    num_of_threads: int
    type: str
    _init_constraints: Tuple[_CST_T, ...]
    identifier: str
    workspace: Path
    width_in_log: int

    @abstractmethod
    def generate_builder(self, privilege_config: PrivilegeConfig, logger_level: int = logging.INFO) -> BaseBuilder:
        pass


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    __slots__ = ('name',)

    name: str

    def generate_builder(self,
                         privilege_config: PrivilegeConfig,
                         logger_level: int = logging.INFO) -> LaunchableBenchmark.Builder:
        from ...benchmark import LaunchableBenchmark
        return LaunchableBenchmark.Builder(self, privilege_config, logger_level)


@dataclass(frozen=True)
class SSHConfig(BenchConfig):
    host: str
    port: Optional[int]
    tunnel: Optional[Dict[str, Any]]
    local_addr: Optional[Tuple[str, int]]
    options: Optional[Dict[str, Any]]

    def generate_builder(self,
                         privilege_config: PrivilegeConfig,
                         logger_level: int = logging.INFO) -> BaseBuilder:
        pass
