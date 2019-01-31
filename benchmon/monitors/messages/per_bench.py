# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import MonitoredMessage

# because of circular import
if TYPE_CHECKING:
    from ...benchmark import BaseBenchmark


@dataclass(frozen=True)
class PerBenchMessage(MonitoredMessage):
    """ :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 를 모니터링한 결과로 생성된 메시지 """
    bench: BaseBenchmark
    """ 대상 벤치마크 """
