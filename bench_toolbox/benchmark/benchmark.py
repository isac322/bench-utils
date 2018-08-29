# coding: UTF-8

from __future__ import annotations

import asyncio
import functools
import logging
import time
from concurrent.futures import CancelledError
from logging import Handler
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

import psutil
from coloredlogs import ColoredFormatter

from .drivers import BenchDriver
from ..containers import BenchConfig
from ..monitors.base_monitor import BaseMonitor
from ..monitors.idle_monitor import IdleMonitor


class Benchmark:
    class _Decorators:
        @staticmethod
        def ensure_running(func: Callable[[Benchmark, Any], Any]):
            @functools.wraps(func)
            def decorator(self: Benchmark, *args, **kwargs):
                if not self.is_running:
                    raise RuntimeError(f'The benchmark ({self._identifier}) has already ended or never been invoked.'
                                       ' Run benchmark first via invoking `run()`!')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_not_running(func: Callable[[Benchmark, Any], Any]):
            @functools.wraps(func)
            def decorator(self: Benchmark, *args, **kwargs):
                if self.is_running:
                    raise RuntimeError(f'benchmark {self._bench_driver.pid} is already in running.')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_invoked(func: Callable[[Benchmark, Any], Any]):
            @functools.wraps(func)
            def decorator(self: Benchmark, *args, **kwargs):
                if not self._bench_driver.has_invoked:
                    raise RuntimeError(f'benchmark {self._identifier} is never invoked.')
                return func(self, *args, **kwargs)

            return decorator

    _file_formatter = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')
    _stream_formatter = ColoredFormatter('%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)14s $ %(message)s')

    def __init__(self,
                 identifier: str,
                 bench_config: BenchConfig,
                 workspace: Path,
                 logger_level: int = logging.INFO,
                 monitors: Tuple[BaseMonitor, ...] = tuple()) -> None:
        self._identifier: str = identifier
        self._bench_driver: BenchDriver = bench_config.generate_driver()

        self._monitors: Tuple[BaseMonitor, ...] = \
            monitors if monitors is not tuple() else (IdleMonitor(self._bench_driver),)

        for monitor in monitors:
            monitor._current_bench = self

        log_parent = workspace / 'logs'
        if not log_parent.exists():
            log_parent.mkdir()

        self._log_path: Path = log_parent / f'{identifier}.log'

        self._end_time: Optional[float] = None

        # setup for loggers

        logger = logging.getLogger(self._identifier)
        logger.setLevel(logger_level)

    @_Decorators.ensure_not_running
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

        logger.info('Starting benchmark...')
        await self._bench_driver.run()
        logger.info(f'The benchmark has started. pid : {self._bench_driver.pid}')

        self.pause()

    @_Decorators.ensure_running
    async def monitor(self) -> None:
        logger = logging.getLogger(self._identifier)

        try:
            await asyncio.wait(tuple(mon.monitor() for mon in self._monitors))

        except CancelledError as e:
            logger.debug(f'The task cancelled : {e}')
            self._stop()

        finally:
            logger.info('The benchmark is ended.')
            self._remove_logger_handlers()
            self._end_time = time.time()

            await asyncio.wait(tuple(mon.on_end() for mon in self._monitors))

    @_Decorators.ensure_running
    def pause(self) -> None:
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    @_Decorators.ensure_running
    def resume(self) -> None:
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()

    def _stop(self) -> None:
        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        try:
            self._bench_driver.stop()
        except (psutil.NoSuchProcess, ProcessLookupError) as e:
            logger.debug(f'Process already killed : {e}')

    def _remove_logger_handlers(self) -> None:
        logger = logging.getLogger(self._identifier)

        for handler in tuple(logger.handlers):  # type: Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    @property
    @_Decorators.ensure_invoked
    def launched_time(self) -> float:
        return self._bench_driver.created_time

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    @property
    def runtime(self) -> Optional[float]:
        if self._end_time is None:
            return None
        elif self._end_time < self.launched_time:
            return None
        else:
            return self._end_time - self.launched_time

    @property
    def is_running(self) -> bool:
        return self._bench_driver.is_running
