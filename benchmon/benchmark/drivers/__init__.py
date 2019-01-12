# coding: UTF-8

from typing import Type

from .base import BenchDriver
from .engines.base import BaseEngine
from .npb import NPBDriver
from .parsec import ParsecDriver
from .rodinia import RodiniaDriver
from .spec import SpecDriver

bench_drivers = (SpecDriver, ParsecDriver, RodiniaDriver, NPBDriver)


def find_driver(workload_name) -> Type[BenchDriver]:
    for _bench_driver in bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def gen_driver(workload_name: str, num_threads: int, engine: BaseEngine) -> BenchDriver:
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, num_threads, engine)
