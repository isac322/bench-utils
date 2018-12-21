# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .base import BasePipeline

if TYPE_CHECKING:
    from ..messages import BaseMessage


class DefaultPipeline(BasePipeline):
    """
    프로토타입으로 멀티 스레드도 아니며, 메시지간의 순서도 지키지 않으며 동작하는 파이프라인.
    추후 이 클래스를 지우고, 각각의 특징이 있는 다른 파이프라인을 개발이 필요함.
    """

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
