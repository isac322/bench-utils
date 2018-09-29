# coding: UTF-8

import json
from asyncio import iscoroutine
from typing import Optional

import aio_pika

from .base import BaseHandler
from ..rabbit_mq import RabbitMQMessage
from ....containers import RabbitMQConfig


class RabbitMQHandler(BaseHandler):
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
        if self._message_queue is not None and self._message_queue.is_closed:
            await self._message_queue.delete()

    async def on_destroy(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            # TODO: this method returns None instead of coroutine
            ret = self._channel.close()

            if iscoroutine(ret):
                await ret

        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
