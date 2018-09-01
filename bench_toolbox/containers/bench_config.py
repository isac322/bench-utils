# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base_config import BaseConfig
from ..benchmark.drivers import gen_driver
from ..benchmark.drivers.base_driver import BenchDriver


@dataclass(frozen=True)
class BenchConfig(BaseConfig):
    name: str
    num_of_threads: int
    bound_cores: str
    mem_bound_sockets: Optional[str]
    cpu_freq: float
    identifier: str

    def generate_driver(self) -> BenchDriver:
        return gen_driver(self.name, self.num_of_threads, self.bound_cores, self.mem_bound_sockets)
