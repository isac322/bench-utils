# coding: UTF-8

from dataclasses import dataclass
from typing import Generator, Tuple

from .base import MonitorConfig


@dataclass(frozen=True)
class PerfEvent:
    """ perf에서 모니터링 할 이벤트의 별명과 perf에서 쓰이는 실제 이벤트 표기법을 묶어서 저장하는 컨테이너. """
    event: str
    """ perf에서 쓰이는 실제 이벤트 표기법 """
    alias: str
    """ 이벤트의 별명 """


@dataclass(frozen=True)
class PerfConfig(MonitorConfig):
    """
    :class:`~benchmon.monitors.perf.PerfMonitor` 객체를 생성할 때 쓰이는 정보.
    어떤 이벤트를 얼만큼의 주기로 모니터링 해야할지가 적혀있다.
    """

    interval: int
    events: Tuple[PerfEvent, ...]

    @property
    def event_names(self) -> Generator[str, None, None]:
        """
        모니터링 할 이벤트들의 별명 (사람이 구분하기 위한 이름) 을 반환한다.

        :return: 모니터링 할 이벤트들의 별명
        :rtype: typing.Generator[str, None, None]
        """
        return (event.alias for event in self.events)

    @property
    def event_str(self) -> str:
        """
        모니터링 할 이벤트들의 실제 perf 표기법들을 ','로 묶은 문자열을 반환한다.

        :return: 모니터링 할 이벤트들의 실제 perf 표기법
        :rtype: str
        """
        return ','.join(event.event for event in self.events)
