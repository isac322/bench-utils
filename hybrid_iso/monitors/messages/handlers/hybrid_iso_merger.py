# coding: UTF-8

from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING, Type, Union

from bench_toolbox.monitors.messages.base import MonitoredMessage
from bench_toolbox.monitors.messages.handlers.base import BaseHandler
from bench_toolbox.monitors.messages.rabbit_mq import RabbitMQMessage
from bench_toolbox.monitors.perf import PerfMonitor
from bench_toolbox.monitors.rdtsc import RDTSCMonitor
from bench_toolbox.monitors.resctrl import ResCtrlMonitor

if TYPE_CHECKING:
    from bench_toolbox.monitors import MonitorData
    from bench_toolbox.monitors.base import BaseMonitor


class HybridIsoMerger(BaseHandler):
    _merge_dict: Dict[Type[BaseMonitor[MonitorData]], Optional[MonitoredMessage]]

    def __init__(self) -> None:
        self._merge_dict = dict.fromkeys((PerfMonitor, RDTSCMonitor, ResCtrlMonitor), None)

    async def on_message(self, message: MonitoredMessage) -> Union[RabbitMQMessage, MonitoredMessage]:
        if not isinstance(message, MonitoredMessage):
            return message

        self._merge_dict[type(message.source)] = message

        if all(self._merge_dict.values()):
            perf_monitor: PerfMonitor = self._merge_dict[PerfMonitor].source

            routing_key = perf_monitor._benchmark.group_name
            data = self._merge_dict[PerfMonitor].data

            data['wall_cycle'] = self._merge_dict[RDTSCMonitor].data

            for key in self._merge_dict[ResCtrlMonitor].data[0].keys():
                data[key] = sum(map(lambda x: x[key], self._merge_dict[ResCtrlMonitor].data))

            ret = RabbitMQMessage(data, self, routing_key)

            for key in self._merge_dict.keys():
                self._merge_dict[key] = None

            return ret
        else:
            return message
