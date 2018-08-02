# coding: UTF-8

from typing import Optional, Type

from benchmark.drivers.base_driver import BenchDriver
from benchmark.drivers.npb_driver import NPBDriver
from benchmark.drivers.parsec_driver import ParsecDriver
from benchmark.drivers.rodinia_driver import RodiniaDriver
from benchmark.drivers.spec_driver import SpecDriver


def find_driver(workload_name) -> Type[BenchDriver]:
    bench_drivers = (SpecDriver, ParsecDriver, RodiniaDriver, NPBDriver)

    for _bench_driver in bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def gen_driver(workload_name: str, num_threads: int, binding_cores: str, numa_cores: Optional[str]) -> BenchDriver:
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, num_threads, binding_cores, numa_cores)
