# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, TypeVar

from ..base_monitor import BaseMonitor

# because of circular import
if TYPE_CHECKING:
    from .handlers.base_handler import BaseHandler

T = TypeVar('T')


@dataclass(frozen=True)
class BaseMessage(Generic[T], metaclass=ABCMeta):
    data: T


@dataclass(frozen=True)
class MonitoredMessage(BaseMessage[T], metaclass=ABCMeta):
    source: BaseMonitor[T]


@dataclass(frozen=True)
class GeneratedMessage(BaseMessage[T], metaclass=ABCMeta):
    generator: BaseHandler
