# coding: UTF-8

from dataclasses import dataclass

from .base_message import BaseMessage


@dataclass(frozen=True)
class SystemMessage(BaseMessage):
    pass
