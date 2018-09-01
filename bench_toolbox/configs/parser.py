# coding: UTF-8

import json
from collections import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple, Union

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


@dataclass(order=True)
class _Pair:
    cfg: Tuple[Any, ...]
    idx: int


def _uniquize(pairs: Iterable[_Pair], max_level: int) -> List[_Pair]:
    sorted_pairs: List[_Pair] = sorted(pairs)

    first_diff: List[Optional[int]] = [1]

    for i in range(1, len(sorted_pairs)):
        elem: Tuple[Any, ...] = sorted_pairs[i].cfg
        prev: Tuple[Any, ...] = sorted_pairs[i - 1].cfg

        curr_level: Optional[int] = None
        for level in range(max_level):
            if elem[level] != prev[level]:
                curr_level = level + 1
                break

        first_diff.append(curr_level)

    first_diff.append(1)

    idx: int = 1
    prev_level: int = first_diff[0]
    while idx <= len(sorted_pairs):
        curr_level: Optional[int] = first_diff[idx]

        if curr_level is None:
            curr_idx = idx

            while first_diff[idx] is None:
                idx += 1

            curr_level = first_diff[idx]

            for same_count, i in enumerate(range(curr_idx, idx + 1)):
                elem: Tuple[Any, ...] = sorted_pairs[i - 1].cfg
                sorted_pairs[i - 1].cfg = elem[:max(prev_level, curr_level)] + (same_count + 1,)

        elif prev_level != max_level or curr_level != max_level:
            elem: Tuple[Any, ...] = sorted_pairs[idx - 1].cfg
            sorted_pairs[idx - 1].cfg = elem[:max(prev_level, curr_level)]

        prev_level = curr_level
        idx += 1

    sorted_pairs.sort(key=lambda x: x.idx)
    return sorted_pairs


def workloads(wl_configs: List[Mapping]) -> Tuple[BenchConfig, ...]:
    pairs: List[_Pair] = (
        _Pair(
                (cfg['name'], cfg['num_of_threads'], cfg['bound_cores'], cfg['mem_bound_sockets'], cfg['cpu_freq']),
                idx
        )
        for idx, cfg in enumerate(wl_configs)
    )

    # name, num_of_threads, bound_cores, mem_bound_sockets, cpu_freq
    max_level = 5

    sorted_pairs = _uniquize(pairs, max_level)

    return tuple(
            BenchConfig(config['name'],
                        config['num_of_threads'],
                        config['bound_cores'],
                        config['mem_bound_sockets'],
                        config['cpu_freq'],
                        '_'.join(map(str, sorted_pairs[idx].cfg)))
            for idx, config in enumerate(wl_configs)
    )
