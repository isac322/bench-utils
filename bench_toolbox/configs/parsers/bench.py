# coding: UTF-8

from __future__ import annotations

from itertools import chain, groupby
from typing import Dict, Iterable, List, Optional, Tuple

from .base import LocalReadParser
from .benchmark.base import BaseBenchParser, BenchJson
from ..containers import BenchConfig


class BenchParser(LocalReadParser[Iterable[BenchConfig]]):
    def _parse(self) -> Iterable[BenchConfig]:
        configs: List[BenchJson] = self._local_config['workloads']
        default_type: Optional[str] = self._local_config.get('default_wl_parser', None)

        configs.sort(key=(lambda x: x.get('parser', default_type)))
        cfg_dict: Dict[str, Tuple[BenchJson, ...]] = {
            bench_type: tuple(cfg_list)
            for bench_type, cfg_list in groupby(configs, lambda x: x.get('parser', default_type))
        }

        return chain(
                *(
                    BaseBenchParser
                        .get_parser(bench_type)
                        .parse(cfg_list, self._workspace)
                    for bench_type, cfg_list in cfg_dict.items()
                )
        )
