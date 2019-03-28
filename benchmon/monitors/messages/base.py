# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, TYPE_CHECKING, Tuple, TypeVar

if TYPE_CHECKING:
    from ..base import BaseMonitor
    # because of circular import
    from .handlers.base import BaseHandler

_MT = TypeVar('_MT')


@dataclass(frozen=True)
class BaseMessage(Generic[_MT], metaclass=ABCMeta):
    """
    모니터 혹은 핸들러에서 생성되어 파이프라인을 통해 핸들러들에게 전달되어지는 메시지.

    .. seealso::

        :mod:`benchmon.monitors` 모듈
            주로 메시지를 만들어내는 모니터

        :mod:`benchmon.monitors.pipelines` 모듈
            메시지가 흐르는 파이프라인

        :mod:`benchmon.monitors.messages.handlers` 모듈
            메시지를 처리하거나 또 다른 메시지를 만들기로 하는 메시지 핸들러
    """
    data: _MT


@dataclass(frozen=True)
class MonitoredMessage(BaseMessage[_MT], Generic[_MT], metaclass=ABCMeta):
    """ :class:`모니터 <benchmon.monitors.base.BaseMonitor>` 를 통해 생성된 메시지 """
    source: BaseMonitor[_MT]
    """ 본 메시지를 생성한 모니터 객체 """


@dataclass(frozen=True)
class MergedMessage(BaseMessage[_MT], Generic[_MT], metaclass=ABCMeta):
    """
    :class:`모니터 <benchmon.monitors.base.BaseMonitor>` 를 통해 생성된 메시지가 다른 모니터에 의해 재가공되고 머지된 메시지.
    """
    source: BaseMonitor[_MT]
    """ 본 메시지를 재가공한 모니터 객체 """
    providers: Tuple[BaseMonitor[_MT], ...]
    level: int = 1
    """ 재가공된 횟수. (e.g. 1: 다른 모니터에서 생성된 데이터를 한번 재가공 함) """


@dataclass(frozen=True)
class GeneratedMessage(BaseMessage[_MT], Generic[_MT], metaclass=ABCMeta):
    """ 모니터가 아닌 :class:`메시지 핸들러 <benchmon.monitors.messages.base.BaseHandler>` 를 통해 생성된 메시지 """
    generator: BaseHandler
    """ 본 메시지를 생성한 핸들러 객체 """
