# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ..base import BaseBenchmark


class BaseConstraint(metaclass=ABCMeta):
    _benchmark: BaseBenchmark

    def __new__(cls: Type[BaseConstraint], bench: BaseBenchmark) -> BaseConstraint:
        obj: BaseConstraint = super().__new__(cls)

        obj._benchmark = bench

        return obj

    async def on_init(self) -> None:
        pass

    @abstractmethod
    async def on_start(self) -> None:
        pass

    @abstractmethod
    async def on_destroy(self) -> None:
        pass
