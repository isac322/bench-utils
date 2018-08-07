# coding: UTF-8

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ..benchmark.drivers import gen_driver
from ..benchmark.drivers.base_driver import BenchDriver


@dataclass(frozen=True)
class BenchConfig:
    name: str
    num_of_threads: int
    binding_cores: str
    numa_nodes: Optional[str]
    cpu_freq: float

    def generate_driver(self) -> BenchDriver:
        return gen_driver(self.name, self.num_of_threads, self.binding_cores, self.numa_nodes)

    @staticmethod
    def gen_identifier(target: 'BenchConfig', configs: Iterable['BenchConfig']) -> str:
        threads_same = True
        cores_same = True
        numa_same = True
        freq_same = True

        index_in_same_cfg = None
        num_of_same_cfg = 0

        for config in configs:
            _all_same = True

            if target.num_of_threads != config.num_of_threads:
                _all_same = threads_same = False
            if target.binding_cores != config.binding_cores:
                _all_same = cores_same = False
            if target.numa_nodes != config.numa_nodes:
                _all_same = numa_same = False
            if target.cpu_freq != config.cpu_freq:
                _all_same = freq_same = False

            if _all_same:
                if target is config:
                    index_in_same_cfg = num_of_same_cfg
                else:
                    num_of_same_cfg += 1

        names: List[str] = [target.name]

        if not threads_same:
            names.append(f'{target.num_of_threads}threads')
        if not cores_same:
            names.append(f'core({target.binding_cores})')
        if not numa_same:
            names.append(f'socket({target.numa_nodes})')
        if not freq_same:
            names.append(f'{target.cpu_freq}GHz')
        if num_of_same_cfg is not 0:
            names.append(str(index_in_same_cfg))

        return '_'.join(names)
