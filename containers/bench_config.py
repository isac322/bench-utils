# coding: UTF-8

from typing import List, Optional

from benchmark.driver.base_driver import BenchDriver, bench_driver


class BenchConfig:
    def __init__(self, workload_name: str, num_of_threads: int, binding_cores: str,
                 numa_mem_nodes: Optional[str], cpu_freq: float, cbm_ranges: str):
        self._workload_name: str = workload_name
        self._num_of_threads: int = num_of_threads
        self._binding_cores: str = binding_cores
        self._numa_mem_nodes: Optional[str] = numa_mem_nodes
        self._cpu_freq: float = cpu_freq
        self._cbm_ranges: str = cbm_ranges

    @property
    def name(self) -> str:
        return self._workload_name

    @property
    def num_of_threads(self) -> int:
        return self._num_of_threads

    @property
    def binding_cores(self) -> str:
        return self._binding_cores

    @property
    def numa_nodes(self) -> Optional[str]:
        return self._numa_mem_nodes

    @property
    def cpu_freq(self) -> float:
        return self._cpu_freq

    @property
    def cbm_ranges(self) -> str:
        return self._cbm_ranges

    def generate_driver(self, identifier: str) -> BenchDriver:
        return bench_driver(self._workload_name, identifier, self._num_of_threads, self._binding_cores,
                            self._numa_mem_nodes, self._cpu_freq, self._cbm_ranges)

    @staticmethod
    def gen_identifier(target: 'BenchConfig', configs: List['BenchConfig']) -> str:
        threads_same = True
        cores_same = True
        numa_same = True
        freq_same = True
        cbm_same = True

        index_in_same_cfg = None
        num_of_same_cfg = 0

        for config in configs:
            _all_same = True

            if target._num_of_threads != config._num_of_threads:
                _all_same = threads_same = False
            if target._binding_cores != config._binding_cores:
                _all_same = cores_same = False
            if target._numa_mem_nodes != config._numa_mem_nodes:
                _all_same = numa_same = False
            if target._cpu_freq != config._cpu_freq:
                _all_same = freq_same = False
            if target.cbm_ranges != config._cbm_ranges:
                _all_same = cbm_same = False

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
        if not cbm_same:
            names.append(f'cbm{target.cbm_ranges}')
        if num_of_same_cfg is not 0:
            names.append(str(index_in_same_cfg))

        return '_'.join(names)
