# coding: UTF-8

from typing import Any, Generator, Tuple


class PerfEvent:
    def __init__(self, event: str, alias: str):
        self._event: str = event
        self._alias: str = alias

    @property
    def event(self) -> str:
        return self._event

    @property
    def alias(self) -> str:
        return self._alias


class PerfConfig:
    def __init__(self, interval: int, events: Tuple[PerfEvent, ...]):
        self._interval: int = interval
        self._events: Tuple[PerfEvent, ...] = events

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def events(self) -> Tuple[PerfEvent, ...]:
        return self._events

    @property
    def event_names(self) -> Generator[str, Any, None]:
        return (event.alias for event in self._events)

    @property
    def event_str(self) -> str:
        return ','.join(event.event for event in self._events)

    def merge_events(self, new_events: Tuple[PerfEvent, ...]) -> 'PerfConfig':
        return PerfConfig(self._interval, self._events + new_events)
