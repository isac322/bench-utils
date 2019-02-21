# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Callable, ClassVar, Iterable, List, TYPE_CHECKING, Tuple, Type, TypeVar

from .base import BaseMonitor, MonitorData
from .base_builder import BaseBuilder
from .messages import BaseMessage, PerBenchMessage
from .oneshot import OneShotMonitor
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context
    # because of circular import
    from .messages import BaseMessage, MonitoredMessage


async def _gen_message(context: Context, monitor: OneShotMonitor[MonitorData]) -> BaseMessage[MonitorData]:
    data = await monitor.monitor_once(context)
    transformed = await monitor._transform_data(data)
    return await monitor.create_message(transformed)


class CombinedOneShotMonitor(BaseMonitor[MonitorData]):
    _interval: float
    _monitors: Iterable[OneShotMonitor[MonitorData]]
    _data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData]

    def __new__(cls: Type[BaseMonitor],
                interval: int,
                monitors: Iterable[OneShotMonitor[MonitorData]],
                data_merger: Callable[[Iterable[MonitoredMessage[MonitorData]]], MonitorData] = None) -> \
            CombinedOneShotMonitor:
        obj: CombinedOneShotMonitor = super().__new__(cls)

        obj._interval = interval / 1000
        obj._monitors = monitors

        if data_merger is None:
            obj._data_merger = CombinedOneShotMonitor._default_merger
        else:
            obj._data_merger = data_merger

        return obj

    async def _monitor(self, context: Context) -> None:
        while True:
            data: List[BaseMessage[MonitorData]] = await asyncio.gather(
                    _gen_message(context, m) for m in self._monitors
            )
            merged = self._data_merger(data)

            message = await self.create_message(merged)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        await asyncio.wait(tuple(mon.stop() for mon in self._monitors))

    async def create_message(self, data: MonitorData) -> PerBenchMessage[MonitorData]:
        # FIXME
        return PerBenchMessage(data, self, None)

    @classmethod
    def _default_merger(cls, data: Iterable[MonitoredMessage[MonitorData]]) -> MonitorData:
        return dict((m.source, m.data) for m in data)

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
                mb.set_benchmark(self._cur_bench)

            monitors: Tuple[OneShotMonitor, ...] = tuple(mb.finalize() for mb in self._monitor_builders)

            return CombinedOneShotMonitor.__new__(CombinedOneShotMonitor,
                                                  self._interval,
                                                  monitors,
                                                  self._data_merger)
