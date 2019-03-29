# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Callable, Iterable, TYPE_CHECKING, Tuple, Union

from .base import BaseMonitor, MonitorData
from .messages import MergedMessage, MonitoredMessage
from .oneshot import OneShotMonitor
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context

_MSG_TYPE = Union[MonitoredMessage[MonitorData], MergedMessage[MonitorData]]
MERGER_TYPE = Callable[[Iterable[_MSG_TYPE]], MonitorData]
_MON_TYPE = OneShotMonitor[MonitorData]


async def _gen_message(context: Context, monitor: _MON_TYPE) -> _MSG_TYPE:
    data = await monitor.monitor_once(context)
    # noinspection PyProtectedMember
    transformed = await monitor._transform_data(data)
    message = await monitor.create_message(context, transformed)

    if isinstance(message, (MonitoredMessage, MergedMessage)):
        return message
    else:
        raise ValueError(f'{message} (from monitor {monitor}) is not an instance of '
                         f'{MonitoredMessage.__class__.__name__}.')


class CombinedOneShotMonitor(BaseMonitor[MonitorData]):
    _interval: float
    _monitors: Tuple[_MON_TYPE, ...]
    _data_merger: MERGER_TYPE

    def __init__(self, interval: int, monitors: Iterable[_MON_TYPE], data_merger: MERGER_TYPE = None) -> None:
        super().__init__()

        self._interval = interval / 1000
        self._monitors = tuple(monitors)

        if data_merger is None:
            self._data_merger = CombinedOneShotMonitor._default_merger
        else:
            self._data_merger = data_merger

    async def _monitor(self, context: Context) -> None:
        while True:
            data: Tuple[_MSG_TYPE] = await asyncio.gather(
                    _gen_message(context, m) for m in self._monitors
            )
            merged = self._data_merger(data)

            message = await self.create_message(context, merged)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        await asyncio.wait(tuple(mon.stop() for mon in self._monitors))

    async def create_message(self, context: Context, data: MonitorData) -> MergedMessage[MonitorData]:
        return MergedMessage(data, self, self._monitors)

    @classmethod
    def _default_merger(cls, data: Iterable[_MSG_TYPE]) -> MonitorData:
        return dict((m.source, m.data) for m in data)
