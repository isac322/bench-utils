# coding: UTF-8

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, TYPE_CHECKING, Tuple, Type

from .base_builder import BaseBuilder
from .iteration_dependent import IterationDependentMonitor
from .messages import PerBenchMessage, SystemMessage
from ..utils import ResCtrl

if TYPE_CHECKING:
    from .messages import MonitoredMessage
    from .. import Context
    # because of circular import
    from ..benchmark import BaseBenchmark

T = Tuple[Mapping[str, int], ...]


class ResCtrlMonitor(IterationDependentMonitor[T]):
    _benchmark: Optional[BaseBenchmark]
    _is_stopped: bool = False
    _group: ResCtrl

    def __new__(cls: Type[ResCtrlMonitor], interval: int, bench: BaseBenchmark = None) -> ResCtrlMonitor:
        obj: ResCtrlMonitor = super().__new__(cls, interval)

        obj._benchmark = bench
        obj._group = ResCtrl()

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        if self._benchmark is not None:
            self._group.group_name = self._benchmark.group_name

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

    async def create_message(self, data: T) -> MonitoredMessage[T]:
        if self._benchmark is None:
            return SystemMessage(data, self)
        else:
            return PerBenchMessage(data, self, self._benchmark)

    async def on_end(self, context: Context) -> None:
        try:
            await self._group.end_read()
        except AssertionError:
            pass

    class Builder(BaseBuilder['ResCtrlMonitor']):
        _interval: int

        def __init__(self, interval: int) -> None:
            super().__init__()
            self._interval = interval

        def _finalize(self) -> ResCtrlMonitor:
            return ResCtrlMonitor.__new__(ResCtrlMonitor, self._interval, self._cur_bench)
