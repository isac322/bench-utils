# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..base import BaseMonitor
    # because of circular import
    from .handlers.base import BaseHandler

T = TypeVar('T')


@dataclass(frozen=True)
class BaseMessage(Generic[T], metaclass=ABCMeta):
    """
    모니터 혹은 핸들러에서 생성되어 파이프라인을 통해 핸들러들에게 전달되어지는 메시지.

    .. seealso::

        :mod:`bench_toolbox.monitors` 모듈
            주로 메시지를 만들어내는 모니터

        :mod:`bench_toolbox.monitors.pipelines` 모듈
            메시지가 흐르는 파이프라인

        :mod:`bench_toolbox.monitors.messages.handlers` 모듈
            메시지를 처리하거나 또 다른 메시지를 만들기로 하는 메시지 핸들러
    """
    data: T


@dataclass(frozen=True)
class MonitoredMessage(BaseMessage[T], metaclass=ABCMeta):
    """ :class:`모니터 <bench_toolbox.monitors.base.BaseMonitor>` 를 통해 생성된 메시지 """
    source: BaseMonitor[T]
    """ 본 메시지를 생성한 모니터 객체 """


@dataclass(frozen=True)
class GeneratedMessage(BaseMessage[T], metaclass=ABCMeta):
    """ 모니터가 아닌 :class:`메시지 핸들러 <bench_toolbox.monitors.messages.base.BaseHandler>` 를 통해 생성된 메시지 """
    generator: BaseHandler
    """ 본 메시지를 생성한 핸들러 객체 """
