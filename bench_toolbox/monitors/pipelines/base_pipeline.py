# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta
from typing import List, Tuple

from ..messages import BaseMessage
from ..messages.handlers.base_handler import BaseHandler


class BasePipeline(metaclass=ABCMeta):
    def __init__(self) -> None:
        self._handlers: List[BaseHandler] = list()

    def add_handler(self, handler: BaseHandler) -> BasePipeline:
        self._handlers.append(handler)

        return self

    async def on_init(self) -> None:
        await asyncio.wait(tuple(handler.on_init() for handler in self._handlers))

    async def on_message(self, message: BaseMessage) -> None:
        for handler in self._handlers:
            message = await handler.on_message(message)

            if message is None:
                break

    async def on_end(self) -> None:
        await asyncio.wait(tuple(handler.on_end() for handler in self._handlers))

    async def on_destroy(self) -> None:
        await asyncio.wait(tuple(handler.on_destroy() for handler in self._handlers))

    @property
    def handlers(self) -> Tuple[BaseHandler]:
        return tuple(self._handlers)
