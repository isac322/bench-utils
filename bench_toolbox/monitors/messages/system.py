# coding: UTF-8

from dataclasses import dataclass

from .base import MonitoredMessage


@dataclass(frozen=True)
class SystemMessage(MonitoredMessage):
    pass
