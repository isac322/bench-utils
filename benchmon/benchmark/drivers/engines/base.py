# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Optional, TYPE_CHECKING, Type

from .... import ContextReadable

if TYPE_CHECKING:
    import asyncio
    from .... import Context


class BaseEngine(ContextReadable, metaclass=ABCMeta):
    """
    :class:`~benchmon.benchmark.drivers.base.BenchDriver` 가 벤치마크를 실행할 때 어떻게 실행할지 서술하는 클래스.

    .. seealso::

        목적과 사용
            :mod:`benchmon.benchmark.drivers.engines` 모듈
    """

    @classmethod
    def of(cls, context: Context) -> Optional[Type[BaseEngine]]:
        # noinspection PyProtectedMember
        for c, v in context._variable_dict.items():
            if issubclass(c, cls):
                return v

        return None

    @classmethod
    @abstractmethod
    async def launch(cls, context: Context, *cmd: str, **kwargs) -> asyncio.subprocess.Process:
        """
        `cmd` 로 주어진 벤치마크 실행 커맨드를 이 클래스의 목적에 맞게 바꾸거나 감싸서 실행한다.

        내부적으로는 asyncio의 subprocess를 사용해야한다.

        :param context: 파이프라인과 모니터링, 벤치마크 실행 조건 등의 정보를 담고있는 객체
        :type context: benchmon.context.Context
        :param cmd: 벤치마크의 실행 커맨드
        :type cmd: typing.Tuple[str, ...]
        :return: 실행 된 워크로드의 객체
        :rtype: asyncio.subprocess.Process
        """
        pass
