# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import CancelledError
from pathlib import Path
from typing import Optional, Tuple, Type

import psutil

from .base_benchmark import BaseBenchmark
from .base_builder import BaseBuilder
from .decorators.benchmark import ensure_invoked, ensure_not_running, ensure_running
from .drivers import BenchDriver
from ..containers import BenchConfig
from ..monitors import MonitorData
from ..monitors.base_builder import BaseBuilder as MonitorBuilder
from ..monitors.base_monitor import BaseMonitor
from ..monitors.idle_monitor import IdleMonitor
from ..monitors.messages.handlers.base_handler import BaseHandler


class Benchmark(BaseBenchmark):
    _bench_config: BenchConfig
    _bench_driver: BenchDriver

    def __new__(cls: Type[Benchmark],
                bench_config: BenchConfig,
                workspace: Path,
                logger_level: int = logging.INFO) -> Benchmark:
        obj: Benchmark = super().__new__(cls, bench_config.identifier, workspace, logger_level)

        obj._bench_config = bench_config
        obj._bench_driver = bench_config.generate_driver()

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    @ensure_not_running
    async def start_and_pause(self, silent: bool = False) -> None:
        self._remove_logger_handlers()

        # setup for loggers

        logger = logging.getLogger(self._identifier)

        fh = logging.FileHandler(self._log_path, mode='w')
        fh.setFormatter(Benchmark._file_formatter)
        logger.addHandler(fh)

        if not silent:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(Benchmark._stream_formatter)
            logger.addHandler(stream_handler)

        # launching benchmark

        if len(self._constraints) is not 0:
            await asyncio.wait(tuple(con.on_init() for con in self._constraints))

        logger.info('Starting benchmark...')
        await self._bench_driver.run()
        logger.info(f'The benchmark has started. pid : {self._bench_driver.pid}')

        self.pause()

    @ensure_running
    async def monitor(self) -> None:
        logger = logging.getLogger(self._identifier)

        monitoring_tasks: Optional[asyncio.Task] = None

        # noinspection PyBroadException
        try:
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_start() for con in self._constraints))

            await asyncio.wait(tuple(mon.on_init() for mon in self._monitors))
            monitoring_tasks = asyncio.create_task(asyncio.wait(tuple(mon.monitor() for mon in self._monitors)))

            await asyncio.wait((self._bench_driver.join(), monitoring_tasks),
                               return_when=asyncio.FIRST_COMPLETED)

            if self.is_running:
                await self._bench_driver.join()
            else:
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except CancelledError as e:
            logger.debug(f'The task cancelled : {e}')
            if self.is_running:
                self._stop()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except Exception as e:
            logger.critical(f'The following errors occurred during monitoring : {e}')
            if self.is_running:
                self._stop()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        finally:
            logger.info('The benchmark is ended.')
            await asyncio.wait(tuple(mon.on_end() for mon in self._monitors))
            await asyncio.wait(tuple(mon.on_destroy() for mon in self._monitors))
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_destroy() for con in self._constraints))

            self._remove_logger_handlers()

    @ensure_running
    def pause(self) -> None:
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    @ensure_running
    def resume(self) -> None:
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()

    @ensure_running
    def _stop(self) -> None:
        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        try:
            self._bench_driver.stop()
        except (psutil.NoSuchProcess, ProcessLookupError) as e:
            logger.debug(f'Process already killed : {e}')

    @property
    @ensure_invoked
    def launched_time(self) -> float:
        return self._bench_driver.created_time

    @property
    @ensure_running
    def pid(self) -> int:
        return self._bench_driver.pid

    @property
    def is_running(self) -> bool:
        return self._bench_driver.is_running

    @property
    def group_name(self) -> str:
        if self.is_running:
            return '{}_{}'.format(self._bench_driver.name, self._bench_driver.pid)
        else:
            return self._identifier

    @ensure_running
    def all_child_tid(self) -> Tuple[int, ...]:
        return self._bench_driver.all_child_tid()

    @ensure_running
    async def join(self) -> None:
        await self._bench_driver.join()

    class Builder(BaseBuilder['Benchmark']):
        def __init__(self,
                     bench_config: BenchConfig,
                     workspace: Path,
                     logger_level: int = logging.INFO) -> None:
            self._cur_obj: Benchmark = Benchmark.__new__(Benchmark, bench_config, workspace, logger_level)

        def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
            return monitor_builder \
                .set_benchmark(self._cur_obj) \
                .set_emitter(self._cur_obj._pipeline.on_message) \
                .finalize()

        def add_handler(self, handler: BaseHandler) -> Benchmark.Builder:
            self._cur_obj._pipeline.add_handler(handler)
            return self

        def _finalize(self) -> None:
            if len(self._monitors) is 0:
                self.build_monitor(IdleMonitor.Builder())
