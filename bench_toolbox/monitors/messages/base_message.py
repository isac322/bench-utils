# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, TypeVar

# because of circular import
if TYPE_CHECKING:
    from ..base_monitor import BaseMonitor

T = TypeVar('T')


@dataclass(frozen=True)
class BaseMessage(Generic[T], metaclass=ABCMeta):
    data: T
    source: BaseMonitor[T]
