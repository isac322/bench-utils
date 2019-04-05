# coding: UTF-8

from typing import Mapping, Tuple, TypeVar

from .base import BaseMonitor
from .combined import CombinedOneShotMonitor
from .idle import IdleMonitor
from .iteration_dependent import IterationDependentMonitor
from .oneshot import OneShotMonitor
from .perf import PerfMonitor
from .power import PowerMonitor
from .rdtsc import RDTSCMonitor
from .resctrl import ResCtrlMonitor
from .runtime import RuntimeMonitor

MonitorData = TypeVar('MonitorData', int, float, Tuple, Mapping)
