# coding: UTF-8

from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING, Type, TypeVar, Union

from benchmon.benchmark import BaseBenchmark
from benchmon.monitors import PerfMonitor, RDTSCMonitor, ResCtrlMonitor, MonitorData
from benchmon.monitors.messages import MonitoredMessage, RabbitMQMessage
from benchmon.monitors.messages.handlers import BaseHandler

if TYPE_CHECKING:
    from benchmon import Context
    from benchmon.monitors import BaseMonitor

_MT = TypeVar('_MT')


class HybridIsoMerger(BaseHandler):
    _merge_dict: Dict[Type[BaseMonitor[MonitorData]], Optional[MonitoredMessage]]

    def __init__(self) -> None:
        self._merge_dict = dict.fromkeys((PerfMonitor, RDTSCMonitor, ResCtrlMonitor), None)

    async def on_message(self,
                         context: Context,
                         message: MonitoredMessage[_MT]) -> Union[RabbitMQMessage, MonitoredMessage[_MT]]:
        if not isinstance(message, MonitoredMessage):
            return message

        self._merge_dict[type(message.source)] = message

        if all(self._merge_dict.values()):
            routing_key = BaseBenchmark.of(context).group_name
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
