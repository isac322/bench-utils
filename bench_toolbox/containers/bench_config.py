# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

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

    def generate_driver(self) -> BenchDriver:
        return gen_driver(self.name, self.num_of_threads, self.bound_cores, self.mem_bound_sockets)

    @classmethod
    def gen_identifier(cls, target: BenchConfig, configs: Iterable[BenchConfig]) -> str:
        threads_not_same = True
        cores_not_same = True
        numa_not_same = True
        freq_not_same = True

        index_in_same_cfg = None
        num_of_same_cfg = 0

        for config in configs:
            _all_same = True

            if target.num_of_threads != config.num_of_threads:
                _all_same = threads_not_same = False
            if target.bound_cores != config.bound_cores:
                _all_same = cores_not_same = False
            if target.mem_bound_sockets != config.mem_bound_sockets:
                _all_same = numa_not_same = False
            if target.cpu_freq != config.cpu_freq:
                _all_same = freq_not_same = False

            if _all_same:
                if target is config:
                    index_in_same_cfg = num_of_same_cfg
                else:
                    num_of_same_cfg += 1

        names: List[str] = [target.name]

        if not threads_not_same:
            names.append(f'{target.num_of_threads}threads')
        if not cores_not_same:
            names.append(f'core({target.bound_cores})')
        if not numa_not_same:
            names.append(f'socket({target.mem_bound_sockets})')
        if not freq_not_same:
            names.append(f'{target.cpu_freq}GHz')
        if num_of_same_cfg is not 0:
            names.append(str(index_in_same_cfg))

        return '_'.join(names)
