# coding: UTF-8

from __future__ import annotations

from itertools import chain, groupby
from typing import Iterable, List, Optional, TYPE_CHECKING

from .base import LocalReadParser
from .benchmark import BaseBenchParser
from ..containers import BenchConfig

if TYPE_CHECKING:
    from .benchmark.base import BenchJson


class BenchParser(LocalReadParser[Iterable[BenchConfig]]):
    """
    `config.json` 에 있는 workload 정보를 읽어서 각 workload에 맞는 파서를 :mod:`benchmon.configs.parsers.benchmark` 에서 찾아
    각각 파싱하고 :class:`benchmon.configs.containers.bench.BenchConfig` 로된 결과를 종합한다.
    """

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
