# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...base import BaseBenchmark


class BaseEngine(metaclass=ABCMeta):
    """
    :class:`~bench_toolbox.benchmark.drivers.base.BenchDriver` 가 벤치마크를 실행할 때 어떻게 실행할 지 서술하는 클래스.

    .. seealso::

        목적과 사용
            :mod:`bench_toolbox.benchmark.drivers.engines` 모듈
    """

    _benchmark: BaseBenchmark

    def __init__(self, benchmark: BaseBenchmark) -> None:
        super().__init__()

        self._benchmark = benchmark

    @abstractmethod
    async def launch(self, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        """
        `cmd` 로 주어진 벤치마크 실행 커맨드를 이 클래스의 목적에 맞게 바꾸거나 감싸서 실행한다.

        내부적으로는 asyncio의 subprocess를 사용해야한다.

        :param cmd: 벤치마크의 실행 커맨드
        :type cmd: typing.Tuple[str, ...]
        :return: 실행 된 워크로드의 객체
        :rtype: asyncio.subprocess.Process
        """
        pass
