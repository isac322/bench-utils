# coding: UTF-8

from dataclasses import dataclass

from .base import HandlerConfig


@dataclass(frozen=True)
class RabbitMQConfig(HandlerConfig):
    """
    :class:`~benchmon.monitors.rabbit_mq.RabbitMQHandler` 객체를 생성할 때 쓰이는 정보.
    메시지를 보낼 호스트 이름과 큐에대한 정보가 담겨있다.
    """
    host_name: str
    creation_q_name: str
