# coding: UTF-8

from __future__ import annotations

from typing import Callable, Coroutine, Type

import rdtsc

from .base_builder import BaseBuilder
from .iteration_dependent_monitor import IterationDependentMonitor
from .messages import BaseMessage
from .messages.system_message import SystemMessage


class RDTSCMonitor(IterationDependentMonitor[int]):
    _prev_data: int

    def __new__(cls: Type[IterationDependentMonitor],
                emitter: Callable[[BaseMessage], Coroutine[None, None, None]],
                interval: int) -> RDTSCMonitor:
        obj: RDTSCMonitor = super().__new__(cls, emitter, interval)

        obj._prev_data = rdtsc.get_cycles()

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use RDTSCMonitor.Builder to instantiate RDTSCMonitor')

    async def on_init(self) -> None:
        await super().on_init()

        self._prev_data = rdtsc.get_cycles()

    def calc_diff(self, before: int, after: int) -> int:
        return after - before

    async def create_message(self, data: int) -> SystemMessage[int]:
        return SystemMessage(data, self)

    async def monitor_once(self) -> int:
        return rdtsc.get_cycles()

    class Builder(BaseBuilder['RDTSCMonitor']):
        _interval: int

        def __init__(self, interval: int) -> None:
            super().__init__()

            self._interval = interval

        def _finalize(self) -> RDTSCMonitor:
            return RDTSCMonitor.__new__(RDTSCMonitor, self._cur_emitter, self._interval)
