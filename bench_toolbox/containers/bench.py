# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

from .base import BaseConfig

# because of circular import
if TYPE_CHECKING:
    from ..benchmark.constraints import BaseBuilder


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    name: str
    num_of_threads: int
    wl_type: str
    constraint_builders: Tuple[BaseBuilder]
    identifier: str
