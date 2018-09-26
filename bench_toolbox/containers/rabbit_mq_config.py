# coding: UTF-8

from dataclasses import dataclass

from .base_config import HandlerConfig


@dataclass(frozen=True)
class RabbitMQConfig(HandlerConfig):
    host_name: str
    creation_q_name: str
