# coding: UTF-8


from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from .base import BaseConstraint
from ..base import BaseBenchmark

T = TypeVar('T', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def finalize(self, benchmark: BaseBenchmark) -> T:
        pass
