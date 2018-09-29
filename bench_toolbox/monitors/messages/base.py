# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..base import BaseMonitor
    # because of circular import
    from .handlers.base import BaseHandler

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
