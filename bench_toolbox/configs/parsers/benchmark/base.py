# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from typing import ClassVar, DefaultDict, Dict, Generic, Iterable, List, MutableMapping, MutableSet, Optional, Set, \
    Tuple, Type, TypeVar, Union

from ...containers import BenchConfig
from ....benchmark.constraints import BaseBuilder, DVFSConstraint, ResCtrlConstraint
from ....benchmark.constraints.cgroup import CpusetConstraint
from ....utils import ResCtrl
from ....utils.hyphen import convert_to_hyphen, convert_to_set
from ....utils.numa_topology import core_to_socket, possible_sockets, socket_to_core

_CT = TypeVar('_CT', bound=BenchConfig)

BenchJson = Dict[str, Union[float, str, int, Tuple[str, ...]]]


class BaseBenchParser(Generic[_CT], metaclass=ABCMeta):
    _entry_prefix_map: ClassVar[MutableMapping[str, str]] = OrderedDict(
            num_of_threads='threads',
            bound_cores='cpus',
            mem_bound_sockets='mems',
            cpu_freq='freq',
            type=''
    )
    _registered_parser: ClassVar[MutableMapping[str, Type[BaseBenchParser]]] = dict()
    _PARSABLE_TYPES: ClassVar[Tuple[str, ...]]

    @staticmethod
    def register_parser(parser: Type[BaseBenchParser]) -> None:
        if not issubclass(parser, BaseBenchParser):
            raise ValueError(f'{parser} is not registrable parser')
        elif not BaseBenchParser._registered_parser.keys().isdisjoint(parser._PARSABLE_TYPES):
            raise ValueError(f'{parser} has types that overlap with existing registered types: '
                             f'{BaseBenchParser._registered_parser.keys() & parser._PARSABLE_TYPES}')

        for parsable_type in parser._PARSABLE_TYPES:
            BaseBenchParser._registered_parser[parsable_type] = parser

    @staticmethod
    def get_parser(bench_type: str) -> Optional[Type[BaseBenchParser]]:
        if bench_type not in BaseBenchParser._registered_parser:
            raise ValueError(f'{bench_type} is not a registered benchmark type')

        return BaseBenchParser._registered_parser[bench_type]

    @classmethod
    @abstractmethod
    def parse(cls, configs: Tuple[BenchJson, ...], workspace: Path) -> Iterable[_CT]:
        pass

    @classmethod
    def _gen_identifier(cls, configs: Tuple[BenchJson, ...], entries: MutableSet[str]) -> None:
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
        elif isinstance(config['cbm_ranges'], str):
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
