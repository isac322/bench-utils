# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, TypeVar

from .base import MonitoredMessage

if TYPE_CHECKING:
    from ...benchmark import BaseBenchmark

_MT = TypeVar('_MT')


@dataclass(frozen=True)
class PerBenchMessage(MonitoredMessage[_MT], Generic[_MT]):
    """ :class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 를 모니터링한 결과로 생성된 메시지 """
    bench: BaseBenchmark
    """ 대상 벤치마크 """
