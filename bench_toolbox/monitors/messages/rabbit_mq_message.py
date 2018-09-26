# coding: UTF-8

from dataclasses import dataclass
from typing import Mapping, Union

from .base_message import GeneratedMessage

_MT = Mapping[str, Union[int, float, str]]


@dataclass(frozen=True)
class RabbitMQMessage(GeneratedMessage[_MT]):
    routing_key: str
