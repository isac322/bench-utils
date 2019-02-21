# coding: UTF-8

from __future__ import annotations

from typing import Dict, List, Mapping, TYPE_CHECKING, Tuple

from .iteration_dependent import IterationDependentMonitor
from .messages import PerBenchMessage, SystemMessage
from ..benchmark import BaseBenchmark
from ..utils import ResCtrl

if TYPE_CHECKING:
    from .messages import MonitoredMessage
    from .. import Context
    # because of circular import

T = Tuple[Mapping[str, int], ...]


class ResCtrlMonitor(IterationDependentMonitor[T]):
    _is_stopped: bool = False
    _group: ResCtrl

    def __init__(self, interval: int) -> None:
        super().__init__(interval)

        self._group = ResCtrl()

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        benchmark = BaseBenchmark.of(context)

        if benchmark is not None:
            self._group.group_name = benchmark.group_name

        await self._group.prepare_to_read()

        self._prev_data = await self.monitor_once(context)

    async def monitor_once(self, context: Context) -> T:
        return await self._group.read()

    @property
    def stopped(self) -> bool:
        return self._is_stopped

    async def stop(self) -> None:
        self._is_stopped = True

    def calc_diff(self, before: T, after: T) -> T:
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

    async def create_message(self, context: Context, data: T) -> MonitoredMessage[T]:
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
