# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TYPE_CHECKING, TypeVar

from .base import BaseConstraint

if TYPE_CHECKING:
    from ..base import BaseBenchmark

T = TypeVar('T', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def finalize(self, benchmark: BaseBenchmark) -> T:
        pass
