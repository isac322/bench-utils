# coding: UTF-8

from __future__ import annotations

from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from typing import ClassVar, DefaultDict, Dict, List, Set, TYPE_CHECKING, Tuple, Union

from ordered_set import OrderedSet

from .base import LocalReadParser
from ..containers import LaunchableConfig
from ...benchmark.constraints import DVFSConstraint, ResCtrlConstraint
from ...benchmark.constraints.cgroup import CpusetConstraint
from ...utils import ResCtrl
from ...utils.hyphen import convert_to_hyphen, convert_to_set
from ...utils.numa_topology import core_to_socket, possible_sockets, socket_to_core

if TYPE_CHECKING:
    from ...benchmark.constraints import BaseBuilder

BenchJson = Dict[str, Union[float, str, int, Tuple[str, ...]]]


class BenchParser(LocalReadParser):
    _name = 'bench'
    TARGET = Tuple[LaunchableConfig, ...]
    _entry_prefix_map: ClassVar[OrderedDict[str, str]] = OrderedDict(
            num_of_threads='threads',
            bound_cores='cpus',
            mem_bound_sockets='mems',
            cpu_freq='freq',
            type=''
    )

    def _parse(self) -> BenchParser.TARGET:
        configs = self._local_config['workloads']

        cfg_dict: Dict[str, List[BenchJson]] = defaultdict(list)
        for cfg in map(self._deduct_config, configs):
            cfg_dict[cfg['name']].append(cfg)
            cfg['identifier'] = cfg['name']

        entries: OrderedSet[str] = OrderedSet(self._entry_prefix_map.keys())
        for name, benches in cfg_dict.items():
            self._gen_identifier(tuple(benches), entries)

            same_count: int = 0
            sorted_cfg = sorted(benches, key=lambda x: x['identifier'])
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

        max_id_len = max(map(lambda x: len(x['identifier']), configs))

        return tuple(
                LaunchableConfig(config['num_of_threads'], config['type'], self._gen_constraints(config),
                                 config['identifier'], self._workspace, max_id_len, config['name'])
                for config in configs
        )

    @classmethod
    def _gen_identifier(cls, configs: Tuple[BenchJson, ...], entries: OrderedSet[str]) -> None:
        counting_dict: Dict[str, DefaultDict[str, List[BenchJson]]] = {e: defaultdict(list) for e in entries}

        for entry, count_map in counting_dict.items():
            for config in configs:
                count_map[config[entry]].append(config)

        selected_key = max(counting_dict.keys(), key=lambda x: len(counting_dict[x]))

        if len(counting_dict[selected_key]) is 1:
            return

        elif len(counting_dict[selected_key]) == len(configs):
            for config in configs:
                config['identifier'] += f'_{cls._entry_prefix_map[selected_key]}={config[selected_key]}'
            return

        else:
            overlapped: List[BenchJson] = list()

            for value, benches in counting_dict[selected_key].items():
                if len(benches) is not 1:
                    overlapped += benches
                    for bench in benches:
                        bench['identifier'] += f'_{cls._entry_prefix_map[selected_key]}={value}'
                    continue

                benches[0]['identifier'] += f'_{cls._entry_prefix_map[selected_key]}={value}'

            entries.remove(selected_key)
            cls._gen_identifier(tuple(overlapped), entries)

    @classmethod
    def _deduct_config(cls, config: BenchJson) -> BenchJson:
        if 'bound_cores' not in config:
            if 'mem_bound_sockets' not in config:
                config['bound_cores'] = Path('/sys/devices/system/cpu/online').read_text().strip()
                config['mem_bound_sockets'] = Path('/sys/devices/system/node/online').read_text().strip()
            else:
                bound_mems = convert_to_set(config['mem_bound_sockets'])
                config['bound_cores'] = \
                    convert_to_hyphen(chain(*(socket_to_core[socket_id] for socket_id in bound_mems)))

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
            start, end = map(int, config['cbm_ranges'].split('-'))
            mask = ResCtrl.gen_mask(start, end)
            config['cbm_ranges'] = tuple(
                    mask if socket_id in sockets else ResCtrl.MIN_MASK for socket_id in possible_sockets()
            )
        else:
            ranges = tuple(
                    ResCtrl.gen_mask(*map(int, _range.split('-')))
                    for _range in config['cbm_ranges']
            )
            config['cbm_ranges'] = ranges

        if 'type' not in config:
            config['type'] = 'fg'

        return config

    @classmethod
    def _gen_constraints(cls, config: BenchJson) -> Tuple[BaseBuilder, ...]:
        constrains: List[BaseBuilder] = list()

        constrains.append(CpusetConstraint.Builder(config['bound_cores'], config['mem_bound_sockets']))
        constrains.append(ResCtrlConstraint.Builder(config['cbm_ranges']))
        # TODO: add CPUConstraint

        if 'cpu_freq' in config:
            cpu_freq: int = int(config['cpu_freq'] * 1_000_000)
            bound_cores = convert_to_set(config['bound_cores'])
            constrains.append(DVFSConstraint.Builder(tuple(bound_cores), cpu_freq))

        return tuple(constrains)
