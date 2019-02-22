# coding: UTF-8

from __future__ import annotations

from itertools import chain, groupby
from typing import Iterable, List, Optional

from .base import LocalReadParser
from .benchmark.base import BaseBenchParser, BenchJson
from ..containers import BenchConfig


# FIXME: rename to ExperimentParser
class BenchParser(LocalReadParser[Iterable[BenchConfig]]):
    def _parse(self) -> Iterable[BenchConfig]:
        configs: List[BenchJson] = self._local_config['workloads']
        default_type: Optional[str] = self._local_config.get('default_wl_parser')

        def _config_key(config: BenchJson):
            return config.get('parser', default_type)

        configs.sort(key=_config_key)

        return chain(
                *(
                    BaseBenchParser
                        .get_parser(bench_type)
                        .parse(tuple(cfg_list), self._workspace)
                    for bench_type, cfg_list in groupby(configs, _config_key)
                )
        )
