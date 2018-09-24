# coding: UTF-8

from dataclasses import dataclass

from .base_message import MonitoredMessage


@dataclass(frozen=True)
class SystemMessage(MonitoredMessage):
    pass
