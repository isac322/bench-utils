# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Callable, Iterable, List, TYPE_CHECKING, Tuple

from .base import BaseMonitor, MonitorData
from .messages import BaseMessage, PerBenchMessage
from .oneshot import OneShotMonitor
from .pipelines.base import BasePipeline
from ..benchmark import BaseBenchmark

if TYPE_CHECKING:
    from .. import Context
    # because of circular import
    from .messages import BaseMessage, MonitoredMessage


async def _gen_message(context: Context, monitor: OneShotMonitor[MonitorData]) -> BaseMessage[MonitorData]:
    data = await monitor.monitor_once(context)
    transformed = await monitor._transform_data(data)
    return await monitor.create_message(context, transformed)


class CombinedOneShotMonitor(BaseMonitor[MonitorData]):
    _interval: float
    _monitors: Tuple[OneShotMonitor[MonitorData], ...]
    _data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData]

    def __init__(self, interval: int, monitors: Iterable[OneShotMonitor[MonitorData]],
                 data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData] = None) -> None:
        super().__init__()

        self._interval = interval / 1000
        self._monitors = tuple(monitors)

        if data_merger is None:
            self._data_merger = CombinedOneShotMonitor._default_merger
        else:
            self._data_merger = data_merger

    async def _monitor(self, context: Context) -> None:
        while True:
            data: List[BaseMessage[MonitorData]] = await asyncio.gather(
                    _gen_message(context, m) for m in self._monitors
            )
            merged = self._data_merger(data)

            message = await self.create_message(context, merged)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        await asyncio.wait(tuple(mon.stop() for mon in self._monitors))

    async def create_message(self, context: Context, data: MonitorData) -> PerBenchMessage[MonitorData]:
        # FIXME
        return PerBenchMessage(data, self, BaseBenchmark.of(context))

    @classmethod
    def _default_merger(cls, data: Iterable[MonitoredMessage[MonitorData]]) -> MonitorData:
        return dict((m.source, m.data) for m in data)
