# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseMessage


class BaseHandler(metaclass=ABCMeta):
    """
    :class:`~bench_toolbox.monitors.pipelines.base.BasePipeline` 에 등록되어서, 그 파이프라인객체에 전달되어지는
    :class:`~bench_toolbox.monitors.messages.base.BaseMessage` 들을 처리하는 핸들러.

    .. note::

        * 이 클래스를 상속받는 핸들러들은 재사용 가능해야한다.
          즉, :meth:`on_init` -> :meth:`on_end` -> :meth:`on_destroy` -> :meth:`on_init` 처럼 같은 핸들러를 재활용할 때
          아무 문제가 없어야한다.

        * 어느 핸들러의 생명주기는 그 핸들러가 속한 파이프라인의 생명주기와 같다.

        * 두 개의 파이프라인에 하나의 핸들러 객체를 등록할 수 없다.
          디자인상 :class:`파이프라인 <bench_toolbox.monitors.pipelines.base.BasePipeline>` 과의 종속성은 없지만,
          :meth:`on_destroy` 같은 메소드의 중복 호출이 발생하기 때문이다.

    .. warning::

        * :class:`~bench_toolbox.monitors.pipelines.base.BasePipeline` 를 상속받아 구현하는 클래스의 내부가 아니라면,
          :meth:`on_init`, :meth:`on_end`, :meth:`on_destroy` 를 임의로 호출해선 안된다.
    """

    async def on_init(self) -> None:
        """
        파이프라인이 시작될 때, 이 핸들러를 초기화 하는 메소드.
        :meth:`on_destroy` 가 호출되기 전까지는 다시 호출될 일이 없다.

        .. note::

            * 보통 이 핸들러객체가 사용할 변수나 설정, 자원등을 초기화하는 코드를 담는다.
        """
        pass

    @abstractmethod
    async def on_message(self, message: BaseMessage) -> Optional[BaseMessage]:
        """
        이전의 핸들러 혹은 파이프라인으로부터 전달받은 메시지를 처리하는 메소드.

        이 메소드의 반환값은 파이프라인의 다음 핸들러에게 전단된다.

        :param message: 파이프라인으로부터 전달받은 메시지 객체
        :type message: BaseMessage
        :return: 같은 파이프라인의 다음 핸들러에게 전달할 메시지 객체. 아무것도 반환하지 않거나 ``None`` 을 반환할 경우,
                 파이프라인에서 ``message`` 는 삭제되며, 다음 핸들러는 아무 메시지 객체도 받지 못한다.
        :rtype: Optional[BaseMessage]
        """
        pass

    async def on_end(self) -> None:
        """
        핸들러의 사용 중지될 때를 처리하는 메소드.

        :meth:`on_destroy` 는 핸들러가 사용하는 자원에 포커스하지만, 이 메소드는 핸들러 기능의 중지에 포커스한다.
        """
        pass

    async def on_destroy(self) -> None:
        """
        핸들러가 종료 이후 정리할 때를 처리하는 메소드.

        :meth:`on_destroy` 는 핸들러 기능의 중지에 포커스하지만, 이 메소드는 핸들러가 사용하는 자원에 포커스한다.
        """
        pass
