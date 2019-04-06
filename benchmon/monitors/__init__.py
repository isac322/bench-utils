# coding: UTF-8

from typing import Mapping, Tuple, TypeVar

from .accumulative import AccumulativeMonitor
from .base import BaseMonitor
from .combined import CombinedOneShotMonitor
from .idle import IdleMonitor
from .interval import IntervalMonitor
from .perf import PerfMonitor
from .power import PowerMonitor
from .rdtsc import RDTSCMonitor
from .resctrl import ResCtrlMonitor
from .runtime import RuntimeMonitor

MonitorData = TypeVar('MonitorData', int, float, Tuple, Mapping)
