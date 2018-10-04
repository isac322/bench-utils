# coding: UTF-8

from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable, List

from ordered_set import OrderedSet

from .base import BaseBenchParser
from ..bench_merger import BenchJson
from ...containers import LaunchableConfig


class LaunchableParser(BaseBenchParser[LaunchableConfig]):
    @classmethod
    def can_handle(cls, config: BenchJson) -> bool:
        return 'name' in config

    @classmethod
    def parse(cls, configs: Iterable[BenchJson], workspace: Path) -> Iterable[LaunchableConfig]:
        cfg_dict: DefaultDict[str, List[BenchJson]] = defaultdict(list)
        for cfg in map(cls._deduct_config, configs):
            cfg_dict[cfg['name']].append(cfg)
            cfg['identifier'] = cfg['name']

        entries: OrderedSet[str] = OrderedSet(cls._entry_prefix_map.keys())
        for benches in cfg_dict.values():
            cls._gen_identifier(tuple(benches), entries)

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

        for config in configs:
            yield LaunchableConfig(config['num_of_threads'], config['type'], cls._gen_constraints(config),
                                   config['identifier'], workspace, max_id_len, config['name'])
