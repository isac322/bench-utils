# coding: UTF-8

from __future__ import annotations

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

from .base import BaseConfig
from ...benchmark import LaunchableBenchmark

if TYPE_CHECKING:
    from pathlib import Path

    from ..containers import PrivilegeConfig
    from ...benchmark import BaseBuilder
    from ...benchmark.constraints import BaseConstraint


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    num_of_threads: int
    type: str
    constraints: Tuple[BaseConstraint, ...]
    identifier: str
    workspace: Path
    width_in_log: int

    @abstractmethod
    def generate_builder(self, privilege_config: PrivilegeConfig, logger_level: int = logging.INFO) -> BaseBuilder:
        pass


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    name: str

    def generate_builder(self, privilege_config: PrivilegeConfig,
                         logger_level: int = logging.INFO) -> LaunchableBenchmark.Builder:
        return LaunchableBenchmark.Builder(self, privilege_config, logger_level)
