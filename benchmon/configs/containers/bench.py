# coding: UTF-8

from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Tuple

from .base import BaseConfig
from ... import ContextReadable
from ...benchmark import BaseBenchmark, LaunchableBenchmark

if TYPE_CHECKING:
    from ..containers import PrivilegeConfig
    from ... import Context
    from ...benchmark.base_builder import BaseBuilder as BenchmarkBuilder
    from ...benchmark.constraints import BaseConstraint


@dataclass(frozen=True)
class BenchConfig(BaseConfig, ContextReadable):
    num_of_threads: int
    type: str
    constraints: Tuple[BaseConstraint, ...]
    identifier: str
    workspace: Path
    width_in_log: int

    @classmethod
    def of(cls, context: Context) -> Optional[BenchConfig]:
        benchmark = BaseBenchmark.of(context)

        if benchmark is None:
            return None
        else:
            # noinspection PyProtectedMember
            return benchmark._bench_config

    @abstractmethod
    def generate_builder(self, privilege_config: PrivilegeConfig, logger_level: int = logging.INFO) -> BenchmarkBuilder:
        pass


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    name: str

    @classmethod
    def of(cls, context: Context) -> Optional[LaunchableConfig]:
        benchmark = LaunchableBenchmark.of(context)
        # noinspection PyProtectedMember
        return benchmark._bench_config

    def generate_builder(self, privilege_config: PrivilegeConfig,
                         logger_level: int = logging.INFO) -> LaunchableBenchmark.Builder:
        return LaunchableBenchmark.Builder(self, privilege_config, logger_level)
