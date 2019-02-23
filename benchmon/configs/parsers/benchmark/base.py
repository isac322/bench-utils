# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from typing import (
    ClassVar, DefaultDict, Dict, Generic, Iterable, List, MutableMapping, MutableSet, Set, Tuple, Type, TypeVar, Union
)

from ...containers import BenchConfig
from ....benchmark.constraints import BaseConstraint, DVFSConstraint, ResCtrlConstraint
from ....benchmark.constraints.cgroup import CpusetConstraint
from ....utils import ResCtrl
from ....utils.hyphen import convert_to_hyphen, convert_to_set
from ....utils.numa_topology import core_to_socket, possible_sockets, socket_to_core

_CT = TypeVar('_CT', bound=BenchConfig)

BenchJson = Dict[str, Union[float, str, int, Tuple[str, ...]]]


class BaseBenchParser(Generic[_CT], metaclass=ABCMeta):
    """
    모든 벤치마크 파서들의 부모 클래스.
    자식 파서 등록이나 설정 validation, 설정 추론, identifier 생성 등 파싱에 필요한 다양한 유틸을 제공한다.

    .. todo::

        * 설정 validation
    """

    _entry_prefix_map: ClassVar[MutableMapping[str, str]] = OrderedDict(
            num_of_threads='threads',
            bound_cores='cpus',
            mem_bound_sockets='mems',
            cpu_freq='freq',
            type=''
    )
    _registered_parser: ClassVar[MutableMapping[str, Type[BaseBenchParser]]] = dict()
    _PARSABLE_TYPES: ClassVar[Tuple[str, ...]]

    @classmethod
    def register_parser(cls, parser: Type[BaseBenchParser]) -> None:
        """
        벤치마크 파서로 `parser` 를 등록한다.
        이 클래스의 모든 자식 클래스는 이 메소드를 통해서 자신을 파서로 등록해야 benchmon에서 자동으로 그 파서를 찾을 수 있다.

        :param parser: 등록할 벤치마크 파서
        :type parser: typing.Type[benchmon.configs.parsers.benchmark.base.BaseBenchParser]
        """
        if not issubclass(parser, BaseBenchParser):
            raise ValueError(f'{parser} is not registrable parser')
        elif not BaseBenchParser._registered_parser.keys().isdisjoint(parser._PARSABLE_TYPES):
            raise ValueError(f'{parser} has types that overlap with existing registered types: '
                             f'{BaseBenchParser._registered_parser.keys() & parser._PARSABLE_TYPES}')

        for parsable_type in parser._PARSABLE_TYPES:
            BaseBenchParser._registered_parser[parsable_type] = parser

    @classmethod
    def get_parser(cls, bench_type: str) -> Type[BaseBenchParser]:
        """
        등록된 파서를 찾아온다.

        :raises ValueError: benchmon에 등록된 파서중에서 `bench_type` 을 파싱 할 수 있는 파서를 찾을 수 없을 때

        :param bench_type: 파서를 찾을 벤치마크 타입
        :type bench_type: str
        :return: 찾아진 `bench_type` 를 파싱할 수 있는 파서
        :rtype: typing.Type[benchmon.configs.parsers.benchmark.base.BaseBenchParser]
        """
        if bench_type not in BaseBenchParser._registered_parser:
            raise ValueError(f'{bench_type} is not a registered benchmark type')

        return BaseBenchParser._registered_parser[bench_type]

    @classmethod
    @abstractmethod
    def parse(cls, configs: Tuple[BenchJson, ...], workspace: Path) -> Iterable[_CT]:
        """
        이 클래스 가 파싱할 수 있는 벤치마크 설정들을 입력으로 받아서 :class:`~benchmon.configs.containers.bench.BenchConfig`
        를 만들어낸다.

        :param configs: 파싱 할 벤치마크 설정들
        :type configs: typing.Tuple[typing.Dict[str, typing.Union[float, str, int, typing.Tuple[str, ...]]], ...]
        :param workspace: `config.json` 이 위치한 폴더의 경로
        :type workspace: pathlib.Path
        :return: 파싱 결과
        :rtype: typing.Iterable[benchmon.configs.containers.bench.BenchConfig]
        """
        pass

    @classmethod
    def _gen_identifier(cls, configs: Tuple[BenchJson, ...], entries: MutableSet[str]) -> None:
        """
        `configs` 에 있는 모든 벤치마크 설정들이 각각의 identifier를 만들 때 까지 재귀적으로 호출되어 identifier를 만들어낸다.
        identifier란, 벤치마크 이름이 같은 경우 서로 구분을 위하여 설정을 읽어서 서로 다른 이름을 붙이는 것이다.
        모든 설정이 같은 경우 번호를 뒤에 붙여 구분한다.

        :param configs: identifier를 붙일 벤치마크 설정들
        :type configs: typing.Tuple[typing.Dict[str, typing.Union[float, str, int, typing.Tuple[str, ...]]], ...]
        :param entries: identifier로 구분할 설정 값 이름들
        :type entries: typing.MutableSet[int]
        """
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
        """
        `config` 에서 일부만 선언되어있거나, 생략된 설정들에 대하여 다른 설정이나 기본값을 참고하여 모든 값을 작성한다.
        추후에 같은일을 다시할 필요를 없애기도하며, 값이 생략된 경우를 처리할 필요를 없앤다.

        :param config: 벤치마크 설정
        :type config: typing.Dict[str, typing.Union[float, str, int, typing.Tuple[str, ...]]]
        :return: 모든 설정값이 채워진 벤치마크 설정
        :rtype: typing.Dict[str, typing.Union[float, str, int, typing.Tuple[str, ...]]]
        """

        # `bound_cores` deduction

        if 'bound_cores' not in config:
            if 'mem_bound_sockets' not in config:
                config['bound_cores'] = Path('/sys/devices/system/cpu/online').read_text().strip()
                config['mem_bound_sockets'] = Path('/sys/devices/system/node/online').read_text().strip()
            else:
                bound_mems = convert_to_set(config['mem_bound_sockets'])
                config['bound_cores'] = \
                    convert_to_hyphen(chain(*(socket_to_core[socket_id] for socket_id in bound_mems)))

        bound_cores = convert_to_set(config['bound_cores'])

        # `num_of_threads` deduction

        if 'num_of_threads' not in config:
            config['num_of_threads'] = len(bound_cores)

        sockets: Set[int] = set(core_to_socket[core_id] for core_id in bound_cores)

        # `mem_bound_sockets` deduction

        if 'mem_bound_sockets' not in config:
            config['mem_bound_sockets'] = convert_to_hyphen(sockets)

        # `cbm_ranges` deduction

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

        # `type` deduction

        if 'type' not in config:
            config['type'] = 'fg'

        return config

    @classmethod
    def _gen_constraints(cls, config: BenchJson) -> Tuple[BaseConstraint, ...]:
        """
        벤치마크 설정을 읽어서 해당하는 :class:`~benchmon.benchmark.constraints.base.BaseConstraint` 를 생성한다.

        :param config: 벤치마크 설정
        :type config: typing.Dict[str, typing.Union[float, str, int, typing.Tuple[str, ...]]]
        :return: 생성된 constraint들
        :rtype: typing.Tuple[benchmon.benchmark.constraints.base.BaseConstraint, ...]
        """
        constrains: List[BaseConstraint] = list()

        constrains.append(CpusetConstraint(config['identifier'], config['bound_cores'], config['mem_bound_sockets']))
        constrains.append(ResCtrlConstraint(config['cbm_ranges']))
        # TODO: add CPUConstraint

        if 'cpu_freq' in config:
            cpu_freq: int = int(config['cpu_freq'] * 1_000_000)
            bound_cores = convert_to_set(config['bound_cores'])
            constrains.append(DVFSConstraint(tuple(bound_cores), cpu_freq))

        return tuple(constrains)
