# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import List, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..messages import BaseMessage
    from ..messages.handlers import BaseHandler


class BasePipeline(metaclass=ABCMeta):
    def __init__(self) -> None:
        self._handlers: List[BaseHandler] = list()

    def add_handler(self, handler: BaseHandler) -> BasePipeline:
        self._handlers.append(handler)

        return self

    @abstractmethod
    async def on_init(self) -> None:
        pass

    @abstractmethod
    async def on_message(self, message: BaseMessage) -> None:
        pass

    @abstractmethod
    async def on_end(self) -> None:
        pass

    @abstractmethod
    async def on_destroy(self) -> None:
        pass

    @property
    def handlers(self) -> Tuple[BaseHandler, ...]:
        return tuple(self._handlers)
