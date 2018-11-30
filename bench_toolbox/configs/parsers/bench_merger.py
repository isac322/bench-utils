# coding: UTF-8

from __future__ import annotations

from collections import defaultdict
from itertools import chain
from pathlib import Path
from typing import DefaultDict, Dict, List, TYPE_CHECKING, Tuple, Type, Union

from .base import LocalReadParser
from ..containers import BenchConfig

if TYPE_CHECKING:
    from .benchmark.base import BaseBenchParser

BenchJson = Dict[str, Union[float, str, int, Tuple[str, ...]]]


class BenchMerger(LocalReadParser[Tuple[BenchConfig, ...]]):
    _parsers: Tuple[Type[BaseBenchParser], ...]

    def __init__(self, workspace: Path, *parser: Type[BaseBenchParser]) -> None:
        super().__init__(workspace)

        self._parsers = tuple(parser)

    def _parse(self) -> Tuple[BenchConfig, ...]:
        configs = self._local_config['workloads']

        cfg_dict: DefaultDict[Type[BaseBenchParser], List[BenchJson]] = defaultdict(list)
        for cfg in configs:
            selected = False

            for parser in self._parsers:
                if parser.can_handle(cfg):
                    cfg_dict[parser].append(cfg)
                    selected = True
                    break

            if not selected:
                raise ValueError(f'Unknown type of config. content : {cfg}')

        return tuple(chain(*(parser.parse(cfg_list, self._workspace) for parser, cfg_list in cfg_dict.items())))
