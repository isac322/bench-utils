# coding: UTF-8

from dataclasses import dataclass

from .base_message import BaseMessage
from ...benchmark import Benchmark


@dataclass(frozen=True)
class PerBenchMessage(BaseMessage):
    bench: Benchmark
