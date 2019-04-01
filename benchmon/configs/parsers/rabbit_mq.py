# coding: UTF-8

from typing import Mapping, Union

from .base import BaseParser
from .. import get_full_path, validate_and_load
from ..containers import RabbitMQConfig


class RabbitMQParser(BaseParser[RabbitMQConfig]):
    """ :mod:`benchmon.configs` 폴더 안에있는 `rabbit_mq.json` 를 읽어 파싱한다. """

    def _parse(self) -> RabbitMQConfig:
        config: Mapping[str, Union[str, Mapping[str, str]]] = validate_and_load(get_full_path('rabbit_mq.json'))

        return RabbitMQConfig(config['host'], config['queue_name']['workload_creation'])
