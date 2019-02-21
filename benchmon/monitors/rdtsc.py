# coding: UTF-8

from __future__ import annotations

from typing import TYPE_CHECKING, Type

import rdtsc

from .base_builder import BaseBuilder
from .iteration_dependent import IterationDependentMonitor
from .messages import SystemMessage

if TYPE_CHECKING:
    from .. import Context


class RDTSCMonitor(IterationDependentMonitor[int]):
    _prev_data: int
    _is_stopped: bool = False

    def __new__(cls: Type[IterationDependentMonitor], interval: int) -> RDTSCMonitor:
        obj: RDTSCMonitor = super().__new__(cls, interval)

        obj._prev_data = rdtsc.get_cycles()

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        self._prev_data = rdtsc.get_cycles()

    def calc_diff(self, before: int, after: int) -> int:
        return after - before

    async def create_message(self, data: int) -> SystemMessage[int]:
        return SystemMessage(data, self)

    async def monitor_once(self, context: Context) -> int:
        return rdtsc.get_cycles()

    @property
    def stopped(self) -> bool:
        return self._is_stopped

    async def stop(self) -> None:
        self._is_stopped = True

    class Builder(BaseBuilder['RDTSCMonitor']):
        _interval: int

        def __init__(self, interval: int) -> None:
            super().__init__()

            self._interval = interval

        def _finalize(self) -> RDTSCMonitor:
            return RDTSCMonitor.__new__(RDTSCMonitor, self._interval)
