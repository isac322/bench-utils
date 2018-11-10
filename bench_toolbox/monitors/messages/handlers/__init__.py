# coding: UTF-8

"""
:mod:`handlers` -- 파이프라인의 메시지 핸들러
=======================================================

:class:`파이프라인 <bench_toolbox.monitors.pipelines.base.BasePipeline>`에 등록되어서 해당 파이프라인에 메시지가 전달될 때
등록된 핸들러들이 순차적으로 메시지를 처리해나간다.


각 핸들러는 독립적이라서 서로에게 영향을 줄 수 있는 방법은, 파이프라이닝하며 전달되는
:class:`메시지 객체 <bench_toolbox.monitors.messages.base.BaseMessage`뿐이다.

.. seealso::

    Module :mod:`bench_toolbox.monitors.pipelines`
        핸들러가 바인딩 되는 파이프라인. 핸들러가 사용되는 방식이 설명 됨.

.. module:: bench_toolbox.monitors.messages.handlers
    :synopsis: 파이프라인 내부에서 메시지를 처리하는 핸들러.
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseHandler
from .printing import PrintHandler
from .rabbit_mq import RabbitMQHandler
