# coding: UTF-8

from __future__ import annotations

from typing import TYPE_CHECKING

from . import MonitorData
from .base import BaseMonitor
from ..benchmark import BaseBenchmark

if TYPE_CHECKING:
    from .messages import BaseMessage
    from .. import Context


class IdleMonitor(BaseMonitor[MonitorData]):
    async def create_message(self, context: Context, data: MonitorData) -> BaseMessage[MonitorData]:
        pass

    async def _monitor(self, context: Context) -> None:
        await BaseBenchmark.of(context).join()

    async def stop(self) -> None:
        pass
