# coding: UTF-8

from typing import Dict, Optional, Type, Union

from .base_handler import BaseHandler
from ..base_message import MonitoredMessage
from ..rabbit_mq_message import RabbitMQMessage
from ... import MonitorData
from ...base_monitor import BaseMonitor
from ...perf_monitor import PerfMonitor
from ...rdtsc_monitor import RDTSCMonitor
from ...resctrl_monitor import ResCtrlMonitor


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
