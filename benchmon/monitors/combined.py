# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Callable, Generic, Iterable, TYPE_CHECKING, Tuple, TypeVar, Union

from .base import BaseMonitor
from .messages import MergedMessage, MonitoredMessage
from .pipelines import BasePipeline

_DAT_T = TypeVar('_DAT_T')
_MSG_TYPE = Union[MonitoredMessage[_DAT_T], MergedMessage[_DAT_T]]
MERGER_TYPE = Callable[[Iterable[_MSG_TYPE]], _DAT_T]

if TYPE_CHECKING:
    from .interval import IntervalMonitor
    from .. import Context

    _MON_T = TypeVar('_MON_T', bound=IntervalMonitor)


async def _gen_message(context: Context, monitor: _MON_T[_DAT_T]) -> _MSG_TYPE:
    data = await monitor.monitor_once(context)
    # noinspection PyProtectedMember
    transformed = await monitor._transform_data(data)
    message = await monitor.create_message(context, transformed)

    if isinstance(message, (MonitoredMessage, MergedMessage)):
        return message
    else:
        raise ValueError(f'{message} (from monitor {monitor}) is not an instance of '
                         f'{MonitoredMessage.__name__} or {MergedMessage.__name__}.')


class CombinedOneShotMonitor(BaseMonitor[MergedMessage, _DAT_T], Generic[_DAT_T]):
    _interval: float
    _monitors: Tuple[_MON_T[_DAT_T], ...]
    _data_merger: MERGER_TYPE

    def __init__(self, interval: int, monitors: Iterable[_MON_T[_DAT_T]], data_merger: MERGER_TYPE = None) -> None:
        super().__init__()

        self._interval = interval / 1000
        self._monitors = tuple(monitors)

        if data_merger is None:
            self._data_merger = CombinedOneShotMonitor._default_merger
        else:
            self._data_merger = data_merger

    async def _monitor(self, context: Context) -> None:
        while True:
            data: Tuple[_MSG_TYPE, ...] = await asyncio.gather(
                    _gen_message(context, m) for m in self._monitors
            )
            merged = self._data_merger(data)

            message = await self.create_message(context, merged)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        await asyncio.wait(tuple(mon.stop() for mon in self._monitors))

    async def create_message(self, context: Context, data: _DAT_T) -> MergedMessage[_DAT_T]:
        return MergedMessage(data, self, self._monitors)

    @classmethod
    def _default_merger(cls, data: Iterable[_MSG_TYPE]) -> _DAT_T:
        return dict((m.source, m.data) for m in data)
