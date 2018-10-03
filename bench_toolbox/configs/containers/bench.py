# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from .base import BaseConfig

# because of circular import
if TYPE_CHECKING:
    from ...benchmark.constraints import BaseBuilder


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    num_of_threads: int
    type: str
    constraint_builders: Tuple[BaseBuilder, ...]
    identifier: str
    workspace: Path


@dataclass(frozen=True)
class LaunchableConfig(BenchConfig):
    name: str
