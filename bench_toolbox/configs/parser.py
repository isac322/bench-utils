# coding: UTF-8

import json
from collections import Mapping
from importlib import resources
from pathlib import Path
from typing import List, Tuple, Union

from ..benchmark.drivers import bench_drivers
from ..containers import BenchConfig, PerfConfig, PerfEvent, RabbitMQConfig


def _validate_and_load(config_file_name: str):
    with resources.path(__package__, config_file_name) as path:
        config_path: Path = path

    if not config_path.is_file():
        raise FileNotFoundError(f'\'{config_path.absolute()}\' does not exist. Please copy a template and modify it')

    with config_path.open() as fp:
        return json.load(fp)


def _parse_bench_home() -> None:
    config: Mapping[str, str] = _validate_and_load('benchmark_home.json')

    for _bench_driver in bench_drivers:
        _bench_driver._bench_home = config[_bench_driver.bench_name]


_parse_bench_home()


def perf() -> PerfConfig:
    config: Mapping[str, Union[int, List[Mapping[str, Union[str, Mapping[str, str]]]]]] = \
        _validate_and_load('perf.json')

    events = tuple(
            PerfEvent(elem, elem)
            if type(elem) is str else
            PerfEvent(elem['event'], elem['alias'])
            for elem in config['events']
    )

    return PerfConfig(config['interval'], events)


def rabbit_mq() -> RabbitMQConfig:
    config: Mapping[str, Union[str, Mapping[str, str]]] = _validate_and_load('rabbit_mq.json')

    return RabbitMQConfig(config['host'], config['queue_name']['workload_creation'])


def workloads(wl_configs: List[Mapping]) -> Tuple[BenchConfig, ...]:
    return tuple(
            BenchConfig(config['name'],
                        config['num_of_threads'],
                        config['bound_cores'],
                        config['mem_bound_sockets'],
                        config['cpu_freq'])
            for config in wl_configs
    )
