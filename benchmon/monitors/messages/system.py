# coding: UTF-8

from dataclasses import dataclass

from .base import MonitoredMessage


@dataclass(frozen=True)
class SystemMessage(MonitoredMessage):
    """
    벤치마크 대신 시스템 레벨로 모니터링한 결과로 생성된 메시지

    .. seealso::
        :class:`benchmon.monitors.messages.per_bench.PerBenchMessage` 클래스
            벤치마크를 모니터링한 결과로 생성된 메시지
    """
    pass
