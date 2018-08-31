# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Tuple

from .base_config import MonitorConfig


@dataclass(frozen=True)
class PerfEvent:
    event: str
    alias: str


@dataclass(frozen=True)
class PerfConfig(MonitorConfig):
    interval: int
    events: Tuple[PerfEvent, ...]

    @property
    def event_names(self) -> Generator[str, Any, None]:
        return (event.alias for event in self.events)

    @property
    def event_str(self) -> str:
        return ','.join(event.event for event in self.events)

    # FIXME
    def merge_events(self, new_events: Tuple[PerfEvent, ...]) -> PerfConfig:
        return PerfConfig(self.interval, self.events + new_events)
