# coding: UTF-8

import asyncio
from typing import Callable, Dict, Iterable, List, Mapping

from . import MonitorData
from .base_monitor import BaseMonitor
from .handlers.base_handler import BaseHandler
from .oneshot_monitor import OneShotMonitor


class CombinedMonitor(BaseMonitor):
    def __init__(self,
                 handlers: Iterable[BaseHandler[MonitorData]],
                 interval: int,
                 monitors: Iterable[OneShotMonitor[MonitorData]],
                 data_merger: Callable[[Iterable[Mapping[str, MonitorData]]], Mapping[str, MonitorData]] = None) \
            -> None:
        super().__init__(handlers)

        self._interval: int = interval
        self._monitors = tuple(monitors)

        if data_merger is None:
            self._data_merger = CombinedMonitor._default_merger
        else:
            self._data_merger = data_merger

    async def _monitor(self) -> None:
        while True:
            data: List[Mapping[str, MonitorData]] = await asyncio.gather(*(m.monitor_once() for m in self._monitors))
            merged = self._data_merger(data)

            await asyncio.wait((*self._handle_data(merged), asyncio.sleep(self._interval)))

    def _handle_data(self, data: Mapping[str, MonitorData]):
        return (h.handle(data) for h in self._handlers)

    @staticmethod
    def _default_merger(data: Iterable[Mapping[str, MonitorData]]) -> Mapping[str, MonitorData]:
        merged: Dict[str, MonitorData] = dict()

        for d in data:
            for k, v in d:
                if k in merged:
                    old_v = merged[k]

                    if isinstance(v, Mapping) and isinstance(old_v, Mapping):
                        merged[k] = CombinedMonitor._default_merger((old_v, v))
                    elif isinstance(v, tuple) and isinstance(old_v, tuple):
                        merged[k] = *old_v, *v
                    else:
                        raise TypeError(f'The resulting data have a duplicate key ({k}) that can not be merged.')
                else:
                    merged[k] = v

        return merged
