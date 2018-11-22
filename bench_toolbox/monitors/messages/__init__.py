# coding: UTF-8

"""
:mod:`messages` -- 파이프라인에 전달되는 메시지
=======================================================

각종 :class:`모니터 <bench_toolbox.monitors.base.BaseMonitor>` 으로부터 최초 생성되어지며,
:class:`파이프라인 <bench_toolbox.monitors.pipelines.base.BasePipeline>` 로 전달되어 해당 파이프라인에 바인딩된
:class:`핸들러 <bench_toolbox.monitors.messages.handlers.base.BaseHandler>` 들에게 차례대로 전달되어 처리된다.

기본적으로 read-only 객체이며, 모니터로부터 생성되거나, 메시지 핸들러로부터 생성될 수 있다.

.. seealso::

    :mod:`bench_toolbox.monitors.pipelines` 모듈
        메시지가 전송되어 처리되는 파이프라인.
        메시지가 사용되는 방식과 재생산되는 방식이 설명 됨.

.. module:: bench_toolbox.monitors.messages
    :synopsis: 모니터로부터 생성돼 파이프라인에 전달되는 메시지
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseMessage, GeneratedMessage, MonitoredMessage
from .per_bench import PerBenchMessage
from .rabbit_mq import RabbitMQMessage
from .system import SystemMessage
