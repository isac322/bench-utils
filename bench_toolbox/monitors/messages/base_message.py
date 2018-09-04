# coding: UTF-8

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TypeVar

# FIXME: circular import
# from ..base_monitor import BaseMonitor

T = TypeVar('T')


@dataclass(frozen=True)
class BaseMessage(Generic[T], metaclass=ABCMeta):
    data: T
    # noinspection PyUnresolvedReferences
    source: 'BaseMonitor[T]'
