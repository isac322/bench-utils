# coding: UTF-8

from __future__ import annotations

from collections import defaultdict
from typing import ClassVar, DefaultDict, Iterable, List, TYPE_CHECKING, Tuple

from ordered_set import OrderedSet

from .base import BaseBenchParser
from ...containers import SSHConfig

if TYPE_CHECKING:
    from pathlib import Path

    from .base import BenchJson


class SSHParser(BaseBenchParser[SSHConfig]):
    _PARSABLE_TYPES: ClassVar[Tuple[str, ...]] = ('ssh',)

    @classmethod
    def _parse(cls, configs: Tuple[BenchJson, ...], workspace: Path) -> Iterable[SSHConfig]:
        cfg_dict: DefaultDict[str, List[BenchJson]] = defaultdict(list)
        for cfg in map(cls._deduct_config, configs):
            cfg_dict[cfg['host']].append(cfg)
            cfg['identifier'] = cfg['host']

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
            yield SSHConfig(
                    config['bench_class'],
                    config['num_of_threads'],
                    config['type'],
                    cls._gen_constraints(config),
                    config['identifier'],
                    workspace,
                    max_id_len,
                    config['host'],
                    config['command'],
                    config.get('port'),
                    config.get('tunnel'),
                    config.get('local_addr'),
                    config.get('options')
            )
