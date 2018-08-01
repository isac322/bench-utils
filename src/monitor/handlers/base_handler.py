# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Generic, Mapping

from monitor.base_monitor import MonitorData


class BaseHandler(Generic[MonitorData], metaclass=ABCMeta):
    @abstractmethod
    async def handle(self, data: Mapping[str, MonitorData]) -> None:
        pass
