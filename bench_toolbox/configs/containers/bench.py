# coding: UTF-8

from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from .base import BaseConfig
from ...benchmark import LaunchableBenchmark

if TYPE_CHECKING:
    from ...benchmark.base_builder import BaseBuilder as BenchmarkBuilder
    # because of circular import
    from ...benchmark.constraints import BaseBuilder


@dataclass(frozen=True)
class BenchConfig(BaseConfig, metaclass=ABCMeta):
    num_of_threads: int
    type: str
    constraint_builders: Tuple[BaseBuilder, ...]
    identifier: str
    workspace: Path
    width_in_log: int

    @abstractmethod
    def generate_builder(self, logger_level: int = logging.INFO) -> BenchmarkBuilder:
        pass


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    name: str

    def generate_builder(self, logger_level: int = logging.INFO) -> LaunchableBenchmark.Builder:
        return LaunchableBenchmark.Builder(self, logger_level)
