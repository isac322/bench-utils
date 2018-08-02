# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Generic, Mapping

from monitors import MonitorData


class BaseHandler(Generic[MonitorData], metaclass=ABCMeta):
    @abstractmethod
    async def handle(self, data: Mapping[str, MonitorData]) -> None:
        pass

    async def on_destroy(self) -> None:
        pass
