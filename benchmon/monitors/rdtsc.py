# coding: UTF-8

from __future__ import annotations

from typing import TYPE_CHECKING

import rdtsc

from .accumulative import AccumulativeMonitor
from .messages import SystemMessage

if TYPE_CHECKING:
    from .. import Context


class RDTSCMonitor(AccumulativeMonitor[SystemMessage, int]):
    __slots__ = ('_prev_data', '_is_stopped')

    _prev_data: int
    _is_stopped: bool

    def __init__(self, interval: int) -> None:
        super().__init__(interval)

        self._prev_data = rdtsc.get_cycles()
        self._is_stopped = False

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        self._prev_data = rdtsc.get_cycles()

    def accumulate(self, before: int, after: int) -> int:
        return after - before

    async def create_message(self, context: Context, data: int) -> SystemMessage[int]:
        return SystemMessage(data, self)

    async def monitor_once(self, context: Context) -> int:
        return rdtsc.get_cycles()

    @property
    def stopped(self) -> bool:
        return self._is_stopped

    async def stop(self) -> None:
        self._is_stopped = True
