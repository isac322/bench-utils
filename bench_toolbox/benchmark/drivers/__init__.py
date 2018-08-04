# coding: UTF-8

import json
from typing import Optional, Type

from bench_toolbox import GLOBAL_CFG_PATH
from .base_driver import BenchDriver
from .npb_driver import NPBDriver
from .parsec_driver import ParsecDriver
from .rodinia_driver import RodiniaDriver
from .spec_driver import SpecDriver

_bench_drivers = (SpecDriver, ParsecDriver, RodiniaDriver, NPBDriver)


def _fetch_bench_path():
    with GLOBAL_CFG_PATH.open() as fp:
        bench_names = json.load(fp)['benchmark']

    for _bench_driver in _bench_drivers:
        _bench_driver._bench_home = bench_names[_bench_driver.bench_name]


_fetch_bench_path()


def find_driver(workload_name) -> Type[BenchDriver]:
    for _bench_driver in _bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def gen_driver(workload_name: str, num_threads: int, binding_cores: str, numa_cores: Optional[str]) -> BenchDriver:
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, num_threads, binding_cores, numa_cores)
