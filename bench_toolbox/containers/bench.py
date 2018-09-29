# coding: UTF-8

from dataclasses import dataclass
from typing import Tuple

from .base import BaseConfig
from ..benchmark.constraints.base_builder import BaseBuilder


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    name: str
    num_of_threads: int
    wl_type: str
    constraint_builders: Tuple[BaseBuilder]
    identifier: str
