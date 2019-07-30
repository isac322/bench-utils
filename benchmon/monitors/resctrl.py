# coding: UTF-8

from __future__ import annotations

from typing import Dict, List, Mapping, TYPE_CHECKING, Tuple

from .accumulative import AccumulativeMonitor
from .messages import MonitoredMessage, PerBenchMessage, SystemMessage
from ..benchmark import BaseBenchmark
from ..utils import ResCtrl

if TYPE_CHECKING:
    from .. import Context

DAT_TYPE = Tuple[Mapping[str, int], ...]


class ResCtrlMonitor(AccumulativeMonitor[MonitoredMessage, DAT_TYPE]):
    __slots__ = ('_is_stopped', '_group')

    _is_stopped: bool
    _group: ResCtrl

    def __init__(self, interval: int) -> None:
        super().__init__(interval)

        self._is_stopped = False
        self._group = ResCtrl()

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        benchmark = BaseBenchmark.of(context)

        if benchmark is not None:
            self._group.group_name = benchmark.group_name

        await self._group.prepare_to_read()

        self._prev_data = await self.monitor_once(context)

    async def monitor_once(self, context: Context) -> DAT_TYPE:
        return await self._group.read()

    @property
    def stopped(self) -> bool:
        return self._is_stopped

    async def stop(self) -> None:
        self._is_stopped = True

    def accumulate(self, before: DAT_TYPE, after: DAT_TYPE) -> DAT_TYPE:
        result: List[Dict[str, int]] = list()

        for idx, d in enumerate(after):
            merged: Dict[str, int] = dict()

            for k, v in d.items():
                # FIXME: hard coded
                if k != 'llc_occupancy':
                    v -= before[idx][k]

                merged[k] = v
            result.append(merged)

        return tuple(result)

    async def create_message(self, context: Context, data: DAT_TYPE) -> MonitoredMessage[DAT_TYPE]:
        benchmark = BaseBenchmark.of(context)

        if benchmark is None:
            return SystemMessage(data, self)
        else:
            return PerBenchMessage(data, self, benchmark)

    async def on_end(self, context: Context) -> None:
        try:
            await self._group.end_read()
        except AssertionError:
            pass
