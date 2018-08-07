# coding: UTF-8

from dataclasses import dataclass


@dataclass(frozen=True)
class RabbitMQConfig:
    host_name: str
    creation_q_name: str
