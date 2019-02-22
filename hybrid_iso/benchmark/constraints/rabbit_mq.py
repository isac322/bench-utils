# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import aio_pika

from benchmon.benchmark.base import BaseBenchmark
from benchmon.benchmark.constraints.base import BaseConstraint
from benchmon.configs.containers import RabbitMQConfig

if TYPE_CHECKING:
    from benchmon import Context


class RabbitMQConstraint(BaseConstraint):
    _creation_q_name: str
    _host: str
    _connection: Optional[aio_pika.Connection] = None
    _channel: Optional[aio_pika.Channel] = None

    def __init__(self, rabbit_mq_config: RabbitMQConfig) -> None:
        self._host = rabbit_mq_config.host_name
        self._creation_q_name = rabbit_mq_config.creation_q_name

    async def on_init(self, context: Context) -> None:
        self._connection = await aio_pika.connect_robust(host=self._host)
        self._channel = await self._connection.channel()

    async def on_start(self, context: Context) -> None:
        await self._channel.declare_queue(self._creation_q_name)

        benchmark = BaseBenchmark.of(context)

        await self._channel.default_exchange.publish(
                aio_pika.Message(f'{benchmark.identifier},{benchmark.type},{benchmark.pid}'.encode()),
                routing_key=self._creation_q_name
        )

    async def on_destroy(self, context: Context) -> None:
        # FIXME: error while closing
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()

        # FIXME: error while closing
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
