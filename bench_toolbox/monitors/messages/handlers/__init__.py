# coding: UTF-8

"""
:mod:`handlers` -- 파이프라인의 메시지 핸들러
=======================================================

:class:`파이프라인 <bench_toolbox.monitors.pipelines.base.BasePipeline>` 에 등록되어서 해당 파이프라인에 메시지가 전달될 때
등록된 핸들러들이 순차적으로 :class:`메시지 <bench_toolbox.monitors.messages.base.BaseMessage>` 를 처리해나간다.

핸들러는 파이프라인에 등록되어 자신에게 주어지는 메시지를 처리하고, 다음 핸들러에게 자신이 받은 메시지를 그대로 전달하거나,
새로운 메시지를 생성하여 보내는 일을 한다.

같은 파이프라인에 등록된 핸들러라고 하더라도, 각 핸들러는 독립적이기 때문에 핸들러끼리 직접적으로 데이터를 주고받는 방법은 존재하지않다.

핸들러는 구현에따라 모든 메시지를 처리하거나, 특정 클래스의 객체만 처리하도록 구현할 수 있다.

.. seealso::

    :mod:`bench_toolbox.monitors.pipelines` 모듈
        핸들러가 바인딩 되는 파이프라인. 핸들러가 사용되는 방식이 설명 됨.

.. module:: bench_toolbox.monitors.messages.handlers
    :synopsis: 파이프라인 내부에서 메시지를 처리하는 핸들러
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseHandler
from .printing import PrintHandler
from .rabbit_mq import RabbitMQHandler
