# coding: UTF-8

from __future__ import annotations

from collections import Mapping
from pathlib import Path
from typing import Dict

from . import get_full_path, validate_and_load
from .parsers.base import BaseParser, LocalReadParser
from ..benchmark.drivers import bench_drivers


def _parse_bench_home() -> None:
    config: Mapping[str, str] = validate_and_load(get_full_path('benchmark_home.json'))

    for _bench_driver in bench_drivers:
        _bench_driver._bench_home = config[_bench_driver.bench_name]


_parse_bench_home()


class Parser:
    _parsers: Dict[str, BaseParser]

    def __init__(self, *parsers: BaseParser) -> None:
        self._parsers = dict()

        for parser in parsers:
            self._parsers[parser.name()] = parser

    def add_parser(self, parser: BaseParser) -> Parser:
        self._parsers[parser.name()] = parser
        return self

    def set_workspace(self, workspace_path: Path) -> Parser:
        local_config = validate_and_load(workspace_path / 'config.json')

        for parser in self._parsers.values():
            if isinstance(parser, LocalReadParser):
                parser.set_local_cfg(local_config)
                parser.workspace = workspace_path

        return self

    def __getitem__(self, parser_name: str) -> BaseParser:
        return self._parsers[parser_name]

    def parse(self, parser_name: str) -> BaseParser.TARGET:
        return self[parser_name].parse()
