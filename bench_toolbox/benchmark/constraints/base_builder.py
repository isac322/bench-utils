# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from .base import BaseConstraint

# FIXME: circular import
# from ..base_benchmark import BaseBenchmark

T = TypeVar('T', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    # noinspection PyUnresolvedReferences
    @abstractmethod
    def finalize(self, benchmark: 'BaseBenchmark') -> T:
        pass
