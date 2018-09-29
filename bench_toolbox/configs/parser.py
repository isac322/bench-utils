# coding: UTF-8

from __future__ import annotations

import json
from collections import Mapping
from dataclasses import dataclass
from importlib import resources
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from ..benchmark.constraints.base_builder import BaseBuilder
from ..benchmark.constraints.cgroup.cpuset import CpusetConstraint
from ..benchmark.constraints.dvfs import DVFSConstraint
from ..benchmark.drivers import bench_drivers
from ..containers import BenchConfig, PerfConfig, PerfEvent, RabbitMQConfig
from ..utils.hyphen import convert_to_hyphen, convert_to_set

PerfConfigJson = Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]
WorkloadJson = Dict[str, Union[float, str, int]]

_socket_id_map: Dict[int, int] = dict()  # core_id: socket_id


def _gen_socket_map() -> None:
    online_node: str = Path('/sys/devices/system/node/online').read_text().strip()

    for socket_id in convert_to_set(online_node):
        cpu_list = Path(f'/sys/devices/system/node/node{socket_id}/cpulist').read_text().strip()

        for core_id in convert_to_set(cpu_list):
            _socket_id_map[core_id] = socket_id


def _get_path(config_file_name: str) -> Path:
    with resources.path(__package__, config_file_name) as path:
        return path


def _validate_and_load(config_path: Path) -> Dict[str, Any]:
    if not config_path.is_file():
        raise FileNotFoundError(f'\'{config_path.absolute()}\' does not exist. Please copy a template and modify it')

    with config_path.open() as fp:
        return json.load(fp)


def _parse_bench_home() -> None:
    config: Mapping[str, str] = _validate_and_load(_get_path('benchmark_home.json'))

    for _bench_driver in bench_drivers:
        _bench_driver._bench_home = config[_bench_driver.bench_name]


_gen_socket_map()
_parse_bench_home()


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


def _gen_bench_config(config: WorkloadJson, identifier: str) -> BenchConfig:
    constrains: List[BaseBuilder] = list()

    if 'bound_cores' not in config:
        config['bound_cores'] = Path('/sys/devices/system/cpu/online').read_text().strip()

    bound_cores = convert_to_set(config['bound_cores'])

    if 'num_of_threads' not in config:
        config['num_of_threads'] = len(bound_cores)

    if 'mem_bound_sockets' not in config:
        sockets: Set[int] = set(_socket_id_map[core_id] for core_id in bound_cores)
        config['mem_bound_sockets'] = convert_to_hyphen(sockets)

    constrains.append(CpusetConstraint.Builder(config['bound_cores'], config['mem_bound_sockets']))
    # TODO: add CPUConstraint

    if 'cpu_freq' in config:
        cpu_freq: int = int(config['cpu_freq'] * 1_000_000)
        constrains.append(DVFSConstraint.Builder(tuple(bound_cores), cpu_freq))

    if 'type' not in config:
        config['type'] = 'fg'

    return BenchConfig(config['name'], config['num_of_threads'], config['type'], tuple(constrains), identifier)


class Parser:
    _cur_local_cfg_path: Optional[Path] = None
    _cur_local_cfg: Optional[Dict] = None
    _perf_config: Optional[PerfConfig] = None
    _rabbit_mq_config: Optional[RabbitMQConfig] = None
    _bench_configs: Optional[Tuple[BenchConfig, ...]] = None

    def _parse_perf(self) -> PerfConfig:
        config: PerfConfigJson = _validate_and_load(_get_path('perf.json'))
        local_config: PerfConfigJson = self._cur_local_cfg.get('perf', dict())

        events = tuple(
                PerfEvent(elem, elem)
                if isinstance(elem, str) else
                PerfEvent(elem['event'], elem['alias'])
                for elem in chain(config['events'], local_config.get('events', tuple()))
        )

        return PerfConfig(local_config.get('interval', config['interval']), events)

    def feed(self, local_config_path: Path) -> Parser:
        self._cur_local_cfg_path = local_config_path
        self._cur_local_cfg = _validate_and_load(local_config_path)
        return self

    def perf_config(self) -> PerfConfig:
        if self._cur_local_cfg_path is None:
            raise AssertionError('feed the local config path first via `feed()`')

        if self._perf_config is None:
            self._perf_config = self._parse_perf()

        return self._perf_config

    def rabbit_mq_config(self) -> RabbitMQConfig:
        if self._rabbit_mq_config is None:
            config: Mapping[str, Union[str, Mapping[str, str]]] = _validate_and_load(_get_path('rabbit_mq.json'))

            self._rabbit_mq_config = RabbitMQConfig(config['host'], config['queue_name']['workload_creation'])

        return self._rabbit_mq_config

    def _parse_workloads(self) -> Tuple[BenchConfig, ...]:
        wl_configs = self._cur_local_cfg['workloads']

        pairs: List[_Pair] = (
            _Pair(
                    (cfg['name'], cfg.get('num_of_threads', None), cfg.get('bound_cores', None),
                     cfg.get('mem_bound_sockets', None), cfg.get('cpu_freq', None)),
                    idx
            )
            for idx, cfg in enumerate(wl_configs)
        )

        # name, num_of_threads, bound_cores, mem_bound_sockets, cpu_freq
        max_level = 5

        sorted_pairs = _uniquize(pairs, max_level)

        return tuple(
                # TODO: add configuration name
                _gen_bench_config(config, '_'.join(map(str, sorted_pairs[idx].cfg)))
                for idx, config in enumerate(wl_configs)
        )

    def parse_workloads(self) -> Tuple[BenchConfig, ...]:
        if self._cur_local_cfg_path is None:
            raise AssertionError('feed the local config path first via `feed()`')

        if self._bench_configs is None:
            self._bench_configs = self._parse_workloads()

        return self._bench_configs
