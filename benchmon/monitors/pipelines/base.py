# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import List, Optional, TYPE_CHECKING, Tuple

from ... import ContextReadable

if TYPE_CHECKING:
    from ..messages import BaseMessage
    from ..messages.handlers import BaseHandler
    from ... import Context


class BasePipeline(ContextReadable, metaclass=ABCMeta):
    """
    :class:`핸들러 <benchmon.monitors.messages.handlers.base.BaseHandler>` 들이 순차적으로 등록 되어지고,
    이 객체에 전달되는 :class:`메시지 <benchmon.monitors.messages.base.BaseMessage>` 들을 처리하는 파이프라인.

    .. note::

        * 이 클래스를 상속받는 핸들러들은 재사용 가능해야한다.
          즉, :meth:`on_init` -> :meth:`on_end` -> :meth:`on_destroy` -> :meth:`on_init` 처럼 같이 파이프라인을 재활용할 때
          아무 문제가 없어야한다.

    .. seealso::

        구현 상황과 해결점
            :mod:`benchmon.monitors.pipelines` 모듈의 note 참조
    """

    @classmethod
    def of(cls, context: Context) -> Optional[BasePipeline]:
        # noinspection PyProtectedMember
        for c, v in context._variable_dict.items():
            if issubclass(c, cls):
                return v

        return None

    def __init__(self) -> None:
        self._handlers: List[BaseHandler] = list()

    def add_handler(self, handler: BaseHandler) -> BasePipeline:
        """
        파이프라인의 맨 끝에 `handler` 를 추가한다.

        .. note::

            * 현재 구현상 모든 파이프라인과 모니터들은 한 스레드에서 실행되기 때문에
              (:mod:`파이프라인 모듈 <benchmon.monitors.pipelines>` 참조),
              이 메소드는 thread-safe할 필요가 없다.
              하지만, 그 기능이 확장될 경우 thread-safe를 고려하도록 수정해야한다.

            * 현재 파이프라인에서 진행되고있는 메시지는 새로 추가되는 핸들러를 사용하지 못하며,
              파이프라인에 다음으로 들어오는 메시지부터 처리 가능하다.

            * 현재 파이프라인 구현상 이미 initialized된 파이프라인에 핸들러를 추가할 경우
              :meth:`~benchmon.monitors.messages.handlers.base.BaseHandler.on_init` 이 호출되지 않는다.

        :param handler: 파이프라인에 추가할 새로운 핸들러
        :type handler: benchmon.monitors.messages.handlers.base.BaseHandler
        :return: Method chaining을 위한 파이프라인 객체 그대로 반환
        :rtype: benchmon.monitors.pipelines.base.BasePipeline
        """
        self._handlers.append(handler)

        return self

    @abstractmethod
    async def on_init(self) -> None:
        """
        파이프라이닝을 처음 시작하거나, destroy된 파이프라인을 재시작할 때 호출되는 메소드.
        :meth:`on_destroy` 가 호출되기 전까지는 다시 호출될 일이 없다.
        """
        pass
        pass

    @abstractmethod
    async def on_message(self, message: BaseMessage) -> None:
        """
        :class:`모니터 <benchmon.monitors.base.BaseMonitor>` 로부터 전달 받은 메시지를 처리하는 메소드.
        파이프라인의 구현마다 메시지를 버퍼링한다던가, 여러개의 메시지를 동시에 파이프라이닝 한다던가 하는 식으로 구현할 수 있다.

        :param message: 모니터로부터 이 파이프라인에 전달되는 메시지
        :type message: benchmon.monitors.messages.base.BaseMessage
        """
        pass

    @abstractmethod
    async def on_end(self) -> None:
        """
        파이프라인이 사용 중지될 때를 처리하는 메소드.

        :meth:`on_destroy` 는 파이프라인이 사용하는 자원에 포커스하지만, 이 메소드는 파이프라인 기능의 중지에 포커스한다.
        """
        pass

    @abstractmethod
    async def on_destroy(self) -> None:
        """
        파이프라인 종료 이후 정리할 때를 처리하는 메소드.

        :meth:`on_destroy` 는 파이프라인 기능의 중지에 포커스하지만, 이 메소드는 파이프라인이 사용하는 자원에 포커스한다.
        """
        pass

    @property
    def handlers(self) -> Tuple[BaseHandler, ...]:
        """
        현재 파이프라인에 등록된 핸들러를 등록된 순서대로 정렬해서 튜플로 반환함

        :return: 현재 파이프라인에 등록된 핸들러. 등록된 순서대로 정렬 됨
        :rtype: Tuple[BaseHandler, ...]
        """
        return tuple(self._handlers)
