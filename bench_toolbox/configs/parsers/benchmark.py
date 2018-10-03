# coding: UTF-8

from __future__ import annotations

from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from typing import DefaultDict, Dict, List, Set, TYPE_CHECKING, Tuple, Union

from ordered_set import OrderedSet

from .base import LocalReadParser
from ..containers import BenchConfig
from ...benchmark.constraints import DVFSConstraint, ResCtrlConstraint
from ...benchmark.constraints.cgroup import CpusetConstraint
from ...utils import ResCtrl
from ...utils.hyphen import convert_to_hyphen, convert_to_set
from ...utils.numa_topology import core_to_socket, possible_sockets, socket_to_core

if TYPE_CHECKING:
    from bench_toolbox.benchmark.constraints import BaseBuilder

WorkloadJson = Dict[str, Union[float, str, int, Tuple[str, ...]]]

entry_prefix_map: OrderedDict[str, str] = OrderedDict(
        num_of_threads='threads',
        bound_cores='cpus',
        mem_bound_sockets='mems',
        cpu_freq='freq',
        type=''
)


def _gen_identifier(configs: Tuple[WorkloadJson, ...], entries: OrderedSet[str]) -> None:
    counting_dict: Dict[str, DefaultDict[str, List[WorkloadJson]]] = {e: defaultdict(list) for e in entries}

    for entry, count_map in counting_dict.items():
        for config in configs:
            count_map[config[entry]].append(config)

    selected_key = max(counting_dict.keys(), key=lambda x: len(counting_dict[x]))

    if len(counting_dict[selected_key]) is 1:
        return

    elif len(counting_dict[selected_key]) == len(configs):
        for config in configs:
            config['identifier'] += f'_{entry_prefix_map[selected_key]}={config[selected_key]}'
        return

    else:
        overlapped: List[WorkloadJson] = list()

        for value, workloads in counting_dict[selected_key].items():
            if len(workloads) is not 1:
                overlapped += workloads
                for workload in workloads:
                    workload['identifier'] += f'_{entry_prefix_map[selected_key]}={value}'
                continue

            workloads[0]['identifier'] += f'_{entry_prefix_map[selected_key]}={value}'

        entries.remove(selected_key)
        _gen_identifier(tuple(overlapped), entries)


def _deduct_bench_config(config: WorkloadJson) -> WorkloadJson:
    if 'bound_cores' not in config:
        if 'mem_bound_sockets' not in config:
            config['bound_cores'] = Path('/sys/devices/system/cpu/online').read_text().strip()
            config['mem_bound_sockets'] = Path('/sys/devices/system/node/online').read_text().strip()
        else:
            bound_mems = convert_to_set(config['mem_bound_sockets'])
            config['bound_cores'] = convert_to_hyphen(chain(*(socket_to_core[socket_id] for socket_id in bound_mems)))

    bound_cores = convert_to_set(config['bound_cores'])

    if 'num_of_threads' not in config:
        config['num_of_threads'] = len(bound_cores)

    sockets: Set[int] = set(core_to_socket[core_id] for core_id in bound_cores)

    if 'mem_bound_sockets' not in config:
        config['mem_bound_sockets'] = convert_to_hyphen(sockets)

    if 'cbm_ranges' not in config:
        config['cbm_ranges'] = tuple(
                ResCtrl.MAX_MASK if socket_id in sockets else ResCtrl.MIN_MASK for socket_id in possible_sockets()
        )

    elif type(config['cbm_ranges']) is str:
        mask = config['cbm_ranges']
        config['cbm_ranges'] = tuple(
                mask if socket_id in sockets else ResCtrl.MIN_MASK for socket_id in possible_sockets()
        )

    if 'type' not in config:
        config['type'] = 'fg'

    return config


def _gen_bench_config(config: WorkloadJson) -> BenchConfig:
    constrains: List[BaseBuilder] = list()

    constrains.append(CpusetConstraint.Builder(config['bound_cores'], config['mem_bound_sockets']))
    constrains.append(ResCtrlConstraint.Builder(config['cbm_ranges']))
    # TODO: add CPUConstraint

    if 'cpu_freq' in config:
        cpu_freq: int = int(config['cpu_freq'] * 1_000_000)
        bound_cores = convert_to_set(config['bound_cores'])
        constrains.append(DVFSConstraint.Builder(tuple(bound_cores), cpu_freq))

    return BenchConfig(config['name'], config['num_of_threads'],
                       config['type'], tuple(constrains), config['identifier'])


class BenchParser(LocalReadParser):
    _name = 'bench'
    TARGET = Tuple[BenchConfig, ...]

    def _parse(self) -> BenchParser.TARGET:
        wl_configs = self._local_config['workloads']

        entries: OrderedSet[str] = OrderedSet(entry_prefix_map.keys())
        wl_dict: Dict[str, List[WorkloadJson]] = defaultdict(list)

        for cfg in map(_deduct_bench_config, wl_configs):
            wl_dict[cfg['name']].append(cfg)
            cfg['identifier'] = cfg['name']

        for name, workloads in wl_dict.items():
            _gen_identifier(tuple(workloads), entries)

            same_count: int = 0
            sorted_cfg = sorted(workloads, key=lambda x: x['identifier'])
            for idx, curr in enumerate(sorted_cfg[1:]):
                prev = sorted_cfg[idx]

                if prev['identifier'] == curr['identifier']:
                    same_count += 1
                    prev['identifier'] += f'_{same_count}'
                elif same_count != 0:
                    prev['identifier'] += f'_{same_count + 1}'
                    same_count = 0
                else:
                    same_count = 0

            if same_count != 0:
                sorted_cfg[-1]['identifier'] += f'_{same_count + 1}'

        return tuple(map(_gen_bench_config, wl_configs))
