# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Callable, ClassVar, Coroutine, Iterable, List, Tuple, Type, TypeVar

from . import MonitorData
from .base import BaseMonitor
from .base_builder import BaseBuilder
from .messages import BaseMessage, MonitoredMessage
from .messages.per_bench import PerBenchMessage
from .oneshot import OneShotMonitor


async def _gen_message(monitor: OneShotMonitor[MonitorData]) -> BaseMessage[MonitorData]:
    data = await monitor.monitor_once()
    transformed = await monitor._transform_data(data)
    return await monitor.create_message(transformed)


class CombinedOneShotMonitor(BaseMonitor[MonitorData]):
    _interval: float
    _monitors: Iterable[OneShotMonitor[MonitorData]]
    _data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData]

    def __new__(cls: Type[BaseMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                interval: int,
                monitors: Iterable[OneShotMonitor[MonitorData]],
                data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData] = None) -> \
            CombinedOneShotMonitor:
        obj: CombinedOneShotMonitor = super().__new__(cls, emitter)

        obj._interval = interval / 1000
        obj._monitors = monitors

        if data_merger is None:
            obj._data_merger = CombinedOneShotMonitor._default_merger
        else:
            obj._data_merger = data_merger

        return obj

    async def _monitor(self) -> None:
        while True:
            data: List[BaseMessage[MonitorData]] = await asyncio.gather(map(_gen_message, self._monitors))
            merged = self._data_merger(data)

            message = await self.create_message(merged)
            self._emitter(message)

            await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        await asyncio.wait(tuple(mon.stop() for mon in self._monitors))

    async def create_message(self, data: MonitorData) -> PerBenchMessage[MonitorData]:
        # FIXME
        return PerBenchMessage(data, self, None)

    @classmethod
    def _default_merger(cls, data: Iterable[MonitoredMessage[MonitorData]]) -> MonitorData:
        return dict((m.source, m.data for m in data))

    class Builder(BaseBuilder['CombinedOneShotMonitor']):
        _T: ClassVar[TypeVar] = TypeVar('_T', bound=OneShotMonitor)

        _monitor_builders: List[BaseBuilder[_T]] = list()
        _interval: int
        _data_merger: Callable[[Iterable[MonitorData]], MonitorData] = None

        def __init__(self, interval: int, data_merger: Callable[[Iterable[MonitorData]], MonitorData] = None) -> None:
            super().__init__()

            self._interval = interval
            self._data_merger = data_merger

        def build_monitor(self, monitor_builder: BaseBuilder[_T]) -> CombinedOneShotMonitor.Builder:
            self._monitor_builders.append(monitor_builder)
            return self

        def _finalize(self) -> CombinedOneShotMonitor:
            for mb in self._monitor_builders:
                mb.set_benchmark(self._cur_bench) \
                    .set_emitter(self._cur_emitter)

            monitors: Tuple[OneShotMonitor] = tuple(mb.finalize() for mb in self._monitor_builders)

            return CombinedOneShotMonitor.__new__(CombinedOneShotMonitor,
                                                  self._cur_emitter,
                                                  self._interval,
                                                  monitors,
                                                  self._data_merger)
