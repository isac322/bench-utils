# coding: UTF-8

from __future__ import annotations

from typing import Callable, Coroutine, Type

import rdtsc

from .base_builder import BaseBuilder
from .base_monitor import SystemMonitor
from .iteration_dependent_monitor import IterationDependentMonitor
from .messages import BaseMessage
from .messages.system_message import SystemMessage


class RDTSCMonitor(IterationDependentMonitor[int], SystemMonitor):
    _prev_data: int

    def __new__(cls: Type[IterationDependentMonitor],
                emitter: Callable[[BaseMessage], Coroutine[None, None, None]],
                interval: int) -> RDTSCMonitor:
        obj: RDTSCMonitor = super().__new__(cls, emitter, interval)

        obj._prev_data = rdtsc.get_cycles()

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def on_init(self) -> None:
        await super().on_init()

        self._prev_data = rdtsc.get_cycles()

    def calc_diff(self, before: int, after: int) -> int:
        return after - before

    async def create_message(self, data: int) -> SystemMessage[int]:
        return SystemMessage(data, self)

    async def monitor_once(self) -> int:
        return rdtsc.get_cycles()

    @property
    def stopped(self) -> bool:
        return self._is_stopped

    def stop(self) -> None:
        self._is_stopped = True

    class Builder(BaseBuilder['RDTSCMonitor']):
        _interval: int

        def __init__(self, interval: int) -> None:
            super().__init__()

            self._interval = interval

        def _finalize(self) -> RDTSCMonitor:
            return RDTSCMonitor.__new__(RDTSCMonitor, self._cur_emitter, self._interval)
