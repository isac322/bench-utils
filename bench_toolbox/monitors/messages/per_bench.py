# coding: UTF-8

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import MonitoredMessage

# because of circular import
if TYPE_CHECKING:
    from ...benchmark import BaseBenchmark


@dataclass(frozen=True)
class PerBenchMessage(MonitoredMessage):
    bench: BaseBenchmark
