# coding: UTF-8

import asyncio
from typing import TYPE_CHECKING

from .base import BasePipeline

if TYPE_CHECKING:
    from ..messages import BaseMessage


class DefaultPipeline(BasePipeline):
    async def on_init(self) -> None:
        if len(self._handlers) is not 0:
            await asyncio.wait(tuple(handler.on_init() for handler in self._handlers))

    async def on_message(self, message: BaseMessage) -> None:
        for handler in self._handlers:
            message = await handler.on_message(message)

            if message is None:
                break

    async def on_end(self) -> None:
        if len(self._handlers) is not 0:
            await asyncio.wait(tuple(handler.on_end() for handler in self._handlers))

    async def on_destroy(self) -> None:
        if len(self._handlers) is not 0:
            await asyncio.wait(tuple(handler.on_destroy() for handler in self._handlers))
