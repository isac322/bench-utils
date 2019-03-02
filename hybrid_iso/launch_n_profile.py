# coding: UTF-8

import argparse
import asyncio
import glob
import logging
import signal
import sys
from itertools import chain
from pathlib import Path
from typing import Iterable, TYPE_CHECKING, Tuple

from benchmon.configs.parsers import BenchParser, PerfParser, RabbitMQParser
from benchmon.monitors import PerfMonitor, PowerMonitor, RDTSCMonitor, ResCtrlMonitor, RuntimeMonitor
from benchmon.monitors.messages.handlers import RabbitMQHandler
from benchmon.utils.hyperthreading import hyper_threading_guard
from .benchmark.constraints.rabbit_mq import RabbitMQConstraint
from .monitors.messages.handlers import HybridIsoMerger, StorePerf, StoreResCtrl, StoreRuntime

if TYPE_CHECKING:
    from benchmon.benchmark import BaseBenchmark
    from benchmon.configs.containers import PerfConfig, RabbitMQConfig

MIN_PYTHON = (3, 7)


async def launch(workspace: Path, silent: bool, verbose: bool) -> bool:
    perf_config: PerfConfig = PerfParser(workspace).parse()
    rabbit_mq_config: RabbitMQConfig = RabbitMQParser().parse()

    benches: Tuple[BaseBenchmark, ...] = tuple(
            bench_cfg.generate_builder(logging.DEBUG if verbose else logging.INFO)
                .add_constraint(RabbitMQConstraint(rabbit_mq_config))
                .add_monitor(RDTSCMonitor(perf_config.interval))
                .add_monitor(ResCtrlMonitor(perf_config.interval))
                .add_monitor(PerfMonitor(perf_config))
                .add_monitor(RuntimeMonitor())
                .add_monitor(PowerMonitor())
                .add_handler(StorePerf())
                .add_handler(StoreRuntime())
                .add_handler(StoreResCtrl())
                # .add_handler(PrintHandler())
                .add_handler(HybridIsoMerger())
                .add_handler(RabbitMQHandler(rabbit_mq_config))
                .finalize()
            for bench_cfg in BenchParser(workspace).parse()
    )

    current_tasks: Tuple[asyncio.Task, ...] = tuple()
    is_cancelled: bool = False

    def cancel_current_tasks() -> None:
        nonlocal current_tasks, is_cancelled
        is_cancelled = True
        for t in current_tasks:  # type: asyncio.Task
            t.cancel()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, cancel_current_tasks)

    async with hyper_threading_guard(False):
        current_tasks = tuple(asyncio.create_task(bench.start_and_pause(silent)) for bench in benches)
        await asyncio.wait(current_tasks)

        if not is_cancelled:
            for bench in benches:
                bench.resume()

            current_tasks = tuple(asyncio.create_task(bench.monitor()) for bench in benches)
            await asyncio.wait(current_tasks)

    loop.remove_signal_handler(signal.SIGINT)

    return not is_cancelled


async def main() -> None:
    if sys.version_info < MIN_PYTHON:
        sys.exit('Python {}.{} or later is required.\n'.format(*MIN_PYTHON))

    parser = argparse.ArgumentParser(description='Launch benchmark written in config file.')
    parser.add_argument('config_dir', metavar='PARENT_DIR_OF_CONFIG_FILE', type=str, nargs='+',
                        help='Directory path where the config file (config.json) exist. (support wildcard *)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print more detail log')
    parser.add_argument('-s', '--silent', action='store_true', help='Do not print any log to stdin.')
    parser.add_argument('--expt-interval', type=int, default=10, help='interval (sec) to sleep between each experiment')

    args = parser.parse_args()

    dirs: Iterable[str] = chain(*(glob.glob(path) for path in args.config_dir))

    silent: bool = args.silent
    verbose: bool = args.verbose
    interval: int = args.expt_interval

    for i, workspace in enumerate(dirs):
        if i is not 0:
            await asyncio.sleep(interval)

        if not await launch(Path(workspace), silent, verbose and not silent):
            break
