# coding: UTF-8

from abc import ABCMeta, abstractmethod


# FIXME: circular import
# from bench_toolbox.benchmark import BaseBenchmark


class BaseConstraint(metaclass=ABCMeta):
    # _benchmark: BaseBenchmark

    # noinspection PyUnresolvedReferences
    def __init__(self, bench: 'BaseBenchmark') -> None:
        super().__init__()

        self._benchmark = bench

    async def on_init(self) -> None:
        pass

    @abstractmethod
    async def on_start(self) -> None:
        pass

    @abstractmethod
    async def on_destroy(self) -> None:
        pass
