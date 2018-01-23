# coding: UTF-8

import asyncio
import json
import logging
import time
from itertools import chain
from logging import Formatter, Handler, LogRecord
from pathlib import Path
from typing import Any, Generator, Optional

import pika
import rdtsc
from coloredlogs import ColoredFormatter

from benchmark.driver.base_driver import BenchDriver
from configs.bench_config import BenchConfig
from configs.perf_config import PerfConfig
from configs.rabbit_mq_config import RabbitMQConfig


class Benchmark:
    _file_formatter = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')
    _stream_formatter = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)14s $ %(message)s')

    def __init__(self, identifier: str, bench_config: BenchConfig,
                 perf_config: PerfConfig, rabbit_mq_config: RabbitMQConfig, workspace: Path):
        self._identifier: str = identifier
        self._run_config: BenchConfig = bench_config
        self._perf_config: PerfConfig = perf_config
        self._rabbit_mq_config: RabbitMQConfig = rabbit_mq_config

        self._bench_driver: Optional[BenchDriver] = None
        self._perf: Optional[asyncio.subprocess.Process] = None
        self._end_time: Optional[float] = None

        perf_parent = workspace / 'perf'
        if not perf_parent.exists():
            perf_parent.mkdir()

        self._perf_csv: Path = perf_parent / f'{identifier}.csv'

        log_parent = workspace / 'logs'
        if not log_parent.exists():
            log_parent.mkdir()

        self._log_path: Path = log_parent / f'{identifier}.log'

        logger = logging.getLogger(self._identifier)
        logger.setLevel(logging.DEBUG)

        metric_logger = logging.getLogger(f'{self._identifier}-rabbitmq')
        metric_logger.setLevel(logging.DEBUG)

    async def create_and_run(self, print_log: bool = False, print_metric_log: bool = False):
        if self._bench_driver is not None and self._bench_driver.is_running:
            raise RuntimeError(f'benchmark {self._bench_driver.pid} is already in running.')

        # setup for logger

        logger = logging.getLogger(self._identifier)

        fh = logging.FileHandler(self._log_path, mode='w')
        fh.setFormatter(Benchmark._file_formatter)
        logger.addHandler(fh)

        if print_log and len(logger.handlers) is 1:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(Benchmark._stream_formatter)
            logger.addHandler(stream_handler)
        elif not print_log and len(logger.handlers) is 2:
            logger.removeHandler(logger.handlers[1])

        # launching benchmark

        self._bench_driver = self._run_config.generate_driver()

        logger.info('Starting benchmark...')
        await self._bench_driver.run()
        logger.info(f'The benchmark has started. pid : {self._bench_driver.pid}')

        # launching perf

        self._perf = perf = await asyncio.create_subprocess_exec(
                'perf', 'stat', '-e', self._perf_config.event_str,
                '-p', str(self._bench_driver.pid), '-x', ',', '-I', str(self._perf_config.interval),
                stderr=asyncio.subprocess.PIPE)

        # setup for metric logger

        rabbit_mq_handler = RabbitMQHandler(self._rabbit_mq_config, self._bench_driver, perf)
        rabbit_mq_handler.setFormatter(RabbitMQFormatter(self._perf_config.event_names))

        metric_logger = logging.getLogger(f'{self._identifier}-rabbitmq')
        metric_logger.addHandler(rabbit_mq_handler)

        if print_metric_log:
            metric_logger.addHandler(logging.StreamHandler())

        with open(self._perf_csv, 'w') as fp:
            fp.write(','.join(chain(self._perf_config.event_names, ('wall-cycles',))) + '\n')
        metric_logger.addHandler(logging.FileHandler(self._perf_csv))

        # perf polling loop

        num_of_events = len(self._perf_config.events)
        stderr: asyncio.StreamReader = perf.stderr

        prev_tsc = rdtsc.get_cycles()
        while self._bench_driver.is_running and perf.returncode is None:
            record = []
            ignore_flag = False

            for _ in range(num_of_events):
                raw_line = await stderr.readline()

                line = raw_line.decode().strip()
                try:
                    value = line.split(',')[1]
                    float(value)
                    record.append(value)
                except (IndexError, ValueError):
                    ignore_flag = True

            tmp = rdtsc.get_cycles()
            record.append(str(tmp - prev_tsc))
            prev_tsc = tmp

            if not ignore_flag:
                metric_logger.info(','.join(record))

        self._end_time = time.time()
        logger.info('The benchmark is ended.')

        if self._perf.returncode is None:
            self._perf.kill()

        handlers = tuple(metric_logger.handlers)
        for handler in handlers:  # type: Handler
            logger.debug(f'removing metric handler {handler}')
            metric_logger.removeHandler(handler)
            try:
                handler.flush()
                handler.close()
            except:
                logger.exception('Exception has happened while removing handler form metric logger.')

        handlers = tuple(logger.handlers)
        for handler in handlers:  # type: Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    def stop(self):
        if self._bench_driver is None or not self._bench_driver.is_running:
            raise RuntimeError(f'benchmark {self._identifier} is already stopped.')

        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        self._bench_driver.stop()
        self._perf.kill()

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
        return self._bench_driver is not None and self._bench_driver.is_running


class RabbitMQHandler(Handler):
    def __init__(self, rabbit_mq_config: RabbitMQConfig, bench_driver: BenchDriver, perf: asyncio.subprocess.Process):
        super().__init__()
        # TODO: upgrade to async version
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_mq_config.host_name))
        self._channel = self._connection.channel()

        self._queue_name: str = f'{bench_driver.name}({bench_driver.pid})'
        self._channel.queue_declare(queue=self._queue_name)

        # Notify creation of this benchmark to scheduler
        self._channel.queue_declare(queue=rabbit_mq_config.creation_q_name)
        self._channel.basic_publish(exchange='', routing_key=rabbit_mq_config.creation_q_name,
                                    body=f'{bench_driver.name},{bench_driver.pid},{perf.pid}')

    def emit(self, record: LogRecord):
        formatted: str = self.format(record)

        self._channel.basic_publish(exchange='', routing_key=self._queue_name, body=formatted)

    def close(self):
        self._channel.queue_delete(self._queue_name)
        self._connection.close()
        super().close()

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return f'<{self.__class__.__name__} {self._queue_name} ({level})>'


class RabbitMQFormatter(Formatter):
    def __init__(self, events: Generator[str, Any, None]):
        super().__init__()
        self._event_names = tuple(events) + ('wall_cycles', 'req_num')
        self._req_num = 0

    @staticmethod
    def _convert_num(val: str):
        try:
            return int(val)
        except ValueError:
            pass

        try:
            return float(val)
        except ValueError:
            raise ValueError(f'{val} is neither an int nor a float.')

    def format(self, record: LogRecord) -> str:
        values = chain(map(self._convert_num, record.msg.split(',')), (self._req_num,))
        self._req_num += 1
        return json.dumps({k: v for k, v in zip(self._event_names, values)})
