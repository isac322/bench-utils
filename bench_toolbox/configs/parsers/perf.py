# coding: UTF-8

from __future__ import annotations

from itertools import chain
from typing import Dict, List, Union

from .base import LocalReadParser
from .. import get_full_path, validate_and_load
from ..containers import PerfConfig, PerfEvent

PerfConfigJson = Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]


class PerfParser(LocalReadParser[PerfConfig]):
    _name = 'perf'

    def _parse(self) -> PerfConfig:
        config: PerfConfigJson = validate_and_load(get_full_path('perf.json'))
        local_config: PerfConfigJson = self._local_config.get('perf', dict(events=tuple()))

        events = tuple(
                PerfEvent(elem, elem)
                if isinstance(elem, str) else
                PerfEvent(elem['event'], elem['alias'])
                for elem in chain(config['events'], local_config['events'])
        )

        return PerfConfig(local_config.get('interval', config['interval']), events)
