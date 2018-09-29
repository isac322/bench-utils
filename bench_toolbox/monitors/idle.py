# coding: UTF-8

from __future__ import annotations

from typing import Callable, Coroutine, Type

from . import MonitorData
from .base import BaseMonitor
from .base_builder import BaseBuilder
from .messages import BaseMessage
from ..benchmark import BaseBenchmark


class IdleMonitor(BaseMonitor[MonitorData]):
    _benchmark: BaseBenchmark

    def __new__(cls: Type[IdleMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                benchmark: BaseBenchmark) -> IdleMonitor:
        obj: IdleMonitor = super().__new__(cls, emitter)

        obj._benchmark = benchmark

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def create_message(self, data: MonitorData) -> BaseMessage[MonitorData]:
        pass

    async def _monitor(self) -> None:
        await self._benchmark.join()

    async def stop(self) -> None:
        pass

    class Builder(BaseBuilder['IdleMonitor']):
        def _finalize(self) -> IdleMonitor:
            return IdleMonitor.__new__(IdleMonitor, self._cur_emitter, self._cur_bench)
