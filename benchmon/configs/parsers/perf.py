# coding: UTF-8

from itertools import chain
from typing import Dict, List, Union

from .base import LocalReadParser
from .. import get_full_path, validate_and_load
from ..containers import PerfConfig, PerfEvent

PerfConfigJson = Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]


class PerfParser(LocalReadParser[PerfConfig]):
    """
    `config.json` 에 있는 perf 설정 정보와 :mod:`benchmon.configs` 폴더 안에 있는 `perf.json` 를 읽어서 내용을 종합한 후
    :class:`benchmon.configs.containers.perf.PerfConfig` 로 파싱한다.

    `perf.json` 의 내용이 기본이며, `config.json` 에서 추가된 event를 추가하거나
    동일한 event 이름의 경우 `perf.json` 의 내용을 덮어 쓴다.
    """

    def _parse(self) -> PerfConfig:
        config: PerfConfigJson = validate_and_load(get_full_path('perf.json'))
        local_config: PerfConfigJson = self._local_config.get('perf', dict(events=tuple()))

        events = tuple(
                PerfEvent(elem, elem)
                if isinstance(elem, str) else
                PerfEvent(elem['event'], elem['alias'])
                for elem in chain(config['events'], local_config.get('events', tuple()))
        )

        return PerfConfig(local_config.get('interval', config['interval']), events)
