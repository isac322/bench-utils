# coding: UTF-8

from __future__ import annotations

from typing import TYPE_CHECKING

import aio_pika

from benchmon.benchmark import BaseBenchmark
from benchmon.benchmark.constraints import BaseConstraint

if TYPE_CHECKING:
    from benchmon import Context
    from benchmon.configs.containers import RabbitMQConfig


class RabbitMQConstraint(BaseConstraint):
    __slots__ = ('_creation_q_name', '_host')

    _creation_q_name: str
    _host: str

    def __init__(self, rabbit_mq_config: RabbitMQConfig) -> None:
        self._host = rabbit_mq_config.host_name
        self._creation_q_name = rabbit_mq_config.creation_q_name

    async def on_start(self, context: Context) -> None:
        connection: aio_pika.Connection = await aio_pika.connect_robust(host=self._host)

        async with connection:
            channel: aio_pika.Channel = await connection.channel()

            await channel.declare_queue(self._creation_q_name)

            benchmark = BaseBenchmark.of(context)
            bench_config = benchmark.bench_config

            await channel.default_exchange.publish(
                    aio_pika.Message(f'{benchmark.identifier},{bench_config.type},{benchmark.pid}'.encode()),
                    routing_key=self._creation_q_name
            )

    async def on_destroy(self, context: Context) -> None:
        pass
