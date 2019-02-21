# coding: UTF-8

from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

import aio_pika

from .base import BaseHandler
from ..rabbit_mq import RabbitMQMessage

if TYPE_CHECKING:
    from ....configs.containers import RabbitMQConfig


class RabbitMQHandler(BaseHandler):
    """
    파이프라인으로 전달되는 메시지 중 :class:`~benchmon.monitors.messages.rabbit_mq.RabbitMQMessage` 객체 혹은 자식 객체
    메시지만 설정된 RabbitMQ 주소로 전송하는 핸들러.

    .. note::

        * :mod:`aio_pika` 를 사용했기 때문에 asynchronous하다.

        * 아직 완벽하게 테스트 되지 못했기 때문에 주의가 필요하다.
    """

    _creation_q_name: str
    _host: str
    _connection: Optional[aio_pika.Connection] = None
    _channel: Optional[aio_pika.Channel] = None
    _message_queue: Optional[aio_pika.Queue] = None

    def __init__(self, rabbit_mq_config: RabbitMQConfig) -> None:
        self._creation_q_name = rabbit_mq_config.creation_q_name
        self._host = rabbit_mq_config.host_name

    async def on_init(self) -> None:
        self._connection = await aio_pika.connect_robust(host=self._host)
        self._channel = await self._connection.channel()

    async def on_message(self, message: RabbitMQMessage) -> Optional[RabbitMQMessage]:
        """
        :class:`~benchmon.monitors.messages.rabbit_mq.RabbitMQMessage` 객체 혹은 자식 객체 메시지만 설정된 큐로 전송한다.
        """

        # ignore non-RabbitMQ messages
        if not isinstance(message, RabbitMQMessage):
            return message

        # FIXME: move initialization
        if self._message_queue is None:
            self._message_queue = await self._channel.declare_queue(message.routing_key, exclusive=True)

        await self._channel.default_exchange.publish(
                aio_pika.Message(
                        body=json.dumps(message.data).encode()
                ),
                routing_key=message.routing_key
        )

    async def on_end(self) -> None:
        if self._message_queue is not None:
            await self._message_queue.delete(if_empty=False)

    async def on_destroy(self) -> None:
        # FIXME: error while closing
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()

        # FIXME: error while closing
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
