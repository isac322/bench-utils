# coding: UTF-8

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any


# FIXME: circular import
# from ..base_monitor import BaseMonitor


@dataclass(frozen=True)
class BaseMessage(metaclass=ABCMeta):
    data: Any
    # noinspection PyUnresolvedReferences
    source: 'BaseMonitor'
