# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod

from ...benchmark import BaseBenchmark


class BaseEngine(metaclass=ABCMeta):
    _benchmark: BaseBenchmark

    def __init__(self, benchmark: BaseBenchmark) -> None:
        super().__init__()

        self._benchmark = benchmark

    @abstractmethod
    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        pass
