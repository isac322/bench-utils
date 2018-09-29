# coding: UTF-8

from dataclasses import dataclass

from .base import MonitoredMessage
from ...benchmark import BaseBenchmark


@dataclass(frozen=True)
class PerBenchMessage(MonitoredMessage):
    bench: BaseBenchmark
