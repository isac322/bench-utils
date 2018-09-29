# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Optional

from ..base import BaseMessage


class BaseHandler(metaclass=ABCMeta):
    async def on_init(self) -> None:
        pass

    @abstractmethod
    async def on_message(self, message: BaseMessage) -> Optional[BaseMessage]:
        pass

    async def on_end(self) -> None:
        pass

    async def on_destroy(self) -> None:
        pass
