# coding: UTF-8

from __future__ import annotations

from typing import Optional, Type

import aio_pika

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ..base import BaseBenchmark
from ...containers import RabbitMQConfig


class RabbitMQConstraint(BaseConstraint):
    _creation_q_name: str
    _host: str
    _connection: Optional[aio_pika.Connection] = None
    _channel: Optional[aio_pika.Channel] = None

    def __new__(cls: Type[RabbitMQConstraint],
                bench: BaseBenchmark, rabbit_mq_config: RabbitMQConfig) -> RabbitMQConstraint:
        obj: RabbitMQConstraint = super().__new__(cls, bench)

        obj._host = rabbit_mq_config.host_name
        obj._creation_q_name = rabbit_mq_config.creation_q_name

        return obj

    async def on_init(self) -> None:
        self._connection = await aio_pika.connect_robust(host=self._host)
        self._channel = await self._connection.channel()

    async def on_start(self) -> None:
        await self._channel.declare_queue(self._creation_q_name)

        await self._channel.default_exchange.publish(
                aio_pika.Message(f'{self._benchmark.identifier},{self._benchmark.type},{self._benchmark.pid}'.encode()),
                routing_key=self._creation_q_name
        )

    async def on_destroy(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()

        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

    class Builder(BaseBuilder['RabbitMQConstraint']):
        _rabbit_mq_config: RabbitMQConfig

        def __init__(self, rabbit_mq_config: RabbitMQConfig) -> None:
            self._rabbit_mq_config = rabbit_mq_config

        def finalize(self, benchmark: BaseBenchmark) -> RabbitMQConstraint:
            return RabbitMQConstraint.__new__(RabbitMQConstraint, benchmark, self._rabbit_mq_config)
