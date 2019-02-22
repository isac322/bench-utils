# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Optional, TYPE_CHECKING, Tuple

from .base import MonitorConfig
from ... import ContextReadable
from ...benchmark import BaseBenchmark
from ...monitors import PerfMonitor

if TYPE_CHECKING:
    from ... import Context


@dataclass(frozen=True)
class PerfEvent:
    event: str
    alias: str


@dataclass(frozen=True)
class PerfConfig(MonitorConfig, ContextReadable):
    interval: int
    events: Tuple[PerfEvent, ...]

    @classmethod
    def of(cls, context: Context) -> Optional[PerfConfig]:
        benchmark = BaseBenchmark.of(context)

        if benchmark is None:
            return None

        # noinspection PyProtectedMember
        for monitor in benchmark._monitors:
            if isinstance(monitor, PerfMonitor):
                # noinspection PyProtectedMember
                return monitor._perf_config

        return None

    @property
    def event_names(self) -> Generator[str, Any, None]:
        return (event.alias for event in self.events)

    @property
    def event_str(self) -> str:
        return ','.join(event.event for event in self.events)
