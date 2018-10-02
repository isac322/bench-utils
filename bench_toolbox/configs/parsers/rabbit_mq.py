# coding: UTF-8

from __future__ import annotations

from typing import Mapping, Union

from .base import BaseParser
from .. import get_full_path, validate_and_load
from ..containers import RabbitMQConfig


class RabbitMQParser(BaseParser):
    _name = 'rabbit_mq'
    TARGET = RabbitMQConfig

    def _parse(self) -> RabbitMQParser.TARGET:
        config: Mapping[str, Union[str, Mapping[str, str]]] = validate_and_load(get_full_path('rabbit_mq.json'))

        return RabbitMQConfig(config['host'], config['queue_name']['workload_creation'])
