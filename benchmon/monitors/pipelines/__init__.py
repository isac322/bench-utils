# coding: UTF-8

"""
:mod:`pipelines` -- 등록된 핸들러를 통해 메시지를 처리
=======================================================

.. TODO: 구조 이미지 삽입

각종 :class:`모니터 <bench_toolbox.monitors.base.BaseMonitor>` 로부터 생성된
:class:`메시지 객체 <bench_toolbox.monitors.messages.base.BaseMessage>` 를 처리하는 파이프라인.

메시지는 파이프라인에 등록된 :class:`핸들러 <bench_toolbox.monitors.messages.handlers.base.BaseHandler>` 들을 순차적으로
거쳐가면서 처리된다.

:class:`메시지 객체 <bench_toolbox.monitors.messages.base.BaseMessage>` 는 read-only 객체이기 때문에,
핸들러를 거쳐가면서 변형될 순 없고, 같은 메시지를 그대로 쓰거나 새로운 메시지 객체를 새로 생성하여 파이프라인에 흐르게할 수 있다.


파이프라인은 기본적으로 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 마다 하나씩 가지며,
시스템 레벨로 단 하나 존재한다.

파이프라인의 의미상, 각 파이프라인끼리의 메시지 교환은 불가능하다.

.. note::

    * 현재 구현상 시스템 레벨 파이프라인은 존재지 않다
    * 현재 구현은 파이프라인과 모니터가 같은 이벤트 루프를 공유한다. 즉, 같은 스레드에서 실행된다.
      모니터나 파이프라인에 연산량이 많아 시간이 오래 걸릴경우, 둘 중 하나가 이벤트 루프를 차지하여 상대방의 수행이 늦어질 수 있다.
        * 현재 파이프라인의 메시지 처리 부분(:meth:`~bench_toolbox.monitors.pipelines.base.BasePipeline.on_message`)을
          바꾸지 않을채로 상위 문제를 해결할 시, 같은 파이프라인에 메시지가 전달되는 순서대로 처리되지 않을 수 있다.
    * 현재 구현상 모든 파이프라인은 같은 이벤트 루프를 공유한다.

.. todo::

    * 시스템 파이프라인 구현
        * **[제안]** 필요하다면, 시스템 파이프라인과 벤치마크의 파이프라인의 결과를 머지하는 부분 구현 (머지를 꼭 해야하는 경우가 있을까?)
    * **[제안]** 로드에따라 파이프라인이 개별적으로 이벤트 루프를 가지도록 구현

.. module:: bench_toolbox.monitors.pipelines
    :synopsis: 모니터로부터 생성된 메시지를 처리
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BasePipeline
from .default import DefaultPipeline
