# coding: UTF-8

import asyncio
import json
import logging
import time
from logging import Formatter, Handler, LogRecord
from pathlib import Path
from typing import Iterable, Optional, Tuple

import pika

from benchmark.driver.base_driver import BenchDriver
from configs.bench_config import BenchConfig
from configs.perf_config import PerfConfig, PerfEvent
from configs.rabbit_mq_config import RabbitMQConfig


class Benchmark:
    def __init__(self, identifier: str, bench_config: BenchConfig,
                 perf_config: PerfConfig, rabbit_mq_config: RabbitMQConfig, workspace: Path):
        self._identifier: str = identifier
        self._run_config: BenchConfig = bench_config
        self._perf_config: PerfConfig = perf_config
        self._rabbit_mq_config: RabbitMQConfig = rabbit_mq_config

        self._bench_driver: Optional[BenchDriver] = None
        self._end_time: Optional[float] = None

        parent = workspace / 'perf'
        if not parent.exists():
            parent.mkdir()

        self._perf_csv: Path = parent / f'{identifier}.csv'

    @asyncio.coroutine
    async def create_and_run(self, no_metric_print: bool = False):
        if self._bench_driver is not None and self._bench_driver.is_running:
            raise RuntimeError(f'benchmark {self._bench_driver.pid} is already in running.')

        self._bench_driver = self._run_config.generate_driver()

        await self._bench_driver.run()

        num_of_events = len(self._perf_config.events)

        perf = await asyncio.create_subprocess_exec(
                'perf', 'stat', '-e', self._perf_config.event_str,
                '-p', str(self._bench_driver.pid), '-x', ',', '-I', str(self._perf_config.interval),
                stderr=asyncio.subprocess.PIPE)

        rabbit_mq_handler = RabbitMQHandler(self._rabbit_mq_config, self._bench_driver)
        rabbit_mq_handler.setFormatter(RabbitMQFormatter(self._perf_config.events))

        logger = logging.getLogger(f'{self._identifier}-rabbitmq')
        logger.setLevel(logging.INFO)
        logger.addHandler(rabbit_mq_handler)
        if not no_metric_print:
            logger.addHandler(logging.StreamHandler())

        with open(self._perf_csv, 'w') as fp:
            fp.write(','.join(self._perf_config.event_names) + '\n')
        logger.addHandler(logging.FileHandler(self._perf_csv))

        stderr: asyncio.StreamReader = perf.stderr

        while self._bench_driver.is_running:
            record = []

            for _ in range(num_of_events):
                raw_line = await stderr.readline()

                if perf.returncode is not None:
                    break
                else:
                    line = raw_line.decode().strip()
                    value = line.split(',')[1]
                    try:
                        float(value)
                    except ValueError:
                        break
                record.append(value)

            if len(record) != num_of_events:
                break
            else:
                logger.info(','.join(record))

        self._end_time = time.time()

        if perf.returncode is None:
            perf.terminate()

        for handler in logger.handlers:  # type: Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    def stop(self):
        if self._bench_driver is None or not self._bench_driver.is_running:
            raise RuntimeError(f'benchmark {self._identifier} is already stopped.')

        self._bench_driver.stop()

    def launched_time(self) -> float:
        if self._bench_driver is None:
            raise RuntimeError(f'benchmark {self._identifier} is never invoked.')

        return self._bench_driver.created_time

    @property
    def identifier(self):
        return self._identifier

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    @property
    def runtime(self) -> Optional[float]:
        if self._end_time is None:
            return None
        else:
            return self._end_time - self.launched_time()

    @property
    def is_running(self):
        return self._bench_driver.is_running


class RabbitMQHandler(Handler):
    def __init__(self, rabbit_mq_config: RabbitMQConfig, bench_driver: BenchDriver):
        super().__init__()
        self._queue_name: str = f'{bench_driver.name}({bench_driver.pid})'
        # TODO: upgrade to async version
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_mq_config.host_name))
        self._channel = self._connection.channel()

        self._channel.queue_declare(queue=self._queue_name)

        # Notify creation of this benchmark to scheduler
        self._channel.queue_declare(queue=rabbit_mq_config.creation_q_name)
        self._channel.basic_publish(exchange='', routing_key=rabbit_mq_config.creation_q_name,
                                    body=f'{bench_driver.pid},{bench_driver.name}')

    def emit(self, record: LogRecord):
        formatted: str = self.format(record)

        self._channel.basic_publish(exchange='', routing_key=self._queue_name, body=formatted)

    def close(self):
        super().close()
        self._channel.queue_delete(self._queue_name)
        self._connection.close()


class RabbitMQFormatter(Formatter):
    def __init__(self, events: Iterable[PerfEvent]):
        super().__init__()
        self._event_names: Tuple[str] = (event.alias for event in events)

    def format(self, record: LogRecord) -> str:
        return json.dumps({k: v for k, v in zip(self._event_names, record.msg.split(','))})
