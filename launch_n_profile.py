#!/usr/bin/env python3
# coding: UTF-8

import argparse
import asyncio
import glob
import logging
import signal
import sys
from itertools import chain
from pathlib import Path
from typing import Tuple

from bench_toolbox.benchmark import Benchmark
from bench_toolbox.benchmark.constraints.rabbit_mq import RabbitMQConstraint
from bench_toolbox.benchmark.constraints.resctrl import ResCtrlConstraint
from bench_toolbox.configs.parser import Parser
from bench_toolbox.monitors.messages.handlers import PrintHandler
from bench_toolbox.monitors.messages.handlers.hybrid_iso_merger import HybridIsoMerger
from bench_toolbox.monitors.messages.handlers.rabbit_mq_handler import RabbitMQHandler
from bench_toolbox.monitors.perf_monitor import PerfMonitor
from bench_toolbox.monitors.power_monitor import PowerMonitor
from bench_toolbox.monitors.rdtsc_monitor import RDTSCMonitor
from bench_toolbox.monitors.resctrl_monitor import ResCtrlMonitor
from bench_toolbox.monitors.runtime_monitor import RuntimeMonitor
from bench_toolbox.utils.hyperthreading import hyper_threading_guard

MIN_PYTHON = (3, 7)


async def launch(workspace: Path,
                 silent: bool,
                 print_metric_log: bool,
                 verbose: bool) -> bool:
    parser = Parser().feed(workspace / 'config.json')
    perf_config = parser.perf_config()
    rabbit_mq_config = parser.rabbit_mq_config()

    benches: Tuple[Benchmark, ...] = tuple(
            Benchmark
                .Builder(bench_cfg, workspace, logging.DEBUG if verbose else logging.INFO)
                .build_constraint(ResCtrlConstraint.Builder(('fffff', 'fffff')))
                .build_constraint(RabbitMQConstraint.Builder(rabbit_mq_config))
                .build_monitor(RDTSCMonitor.Builder(perf_config.interval))
                .build_monitor(ResCtrlMonitor.Builder(perf_config.interval))
                .build_monitor(PerfMonitor.Builder(perf_config))
                .build_monitor(RuntimeMonitor.Builder())
                .build_monitor(PowerMonitor.Builder())
                .add_handler(HybridIsoMerger())
                #.add_handler(PrintHandler())
                .add_handler(RabbitMQHandler(rabbit_mq_config))
                .finalize()
            for bench_cfg in parser.parse_workloads()
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

            await asyncio.sleep(0.1)

            current_tasks = tuple(asyncio.create_task(bench.monitor()) for bench in benches)
            await asyncio.wait(current_tasks)

    loop.remove_signal_handler(signal.SIGINT)

    return not is_cancelled


async def main() -> None:
    parser = argparse.ArgumentParser(description='Launch benchmark written in config file.')
    parser.add_argument('config_dir', metavar='PARENT_DIR_OF_CONFIG_FILE', type=str, nargs='+',
                        help='Directory path where the config file (config.json) exist. (support wildcard *)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print more detail log')
    parser.add_argument('-S', '--silent', action='store_true', help='Do not print any log to stdin. (override -M)')
    parser.add_argument('-M', '--print-metric-log', action='store_true',
                        help='Print all metric related logs to stdout.')
    parser.add_argument('--expt-interval', type=int, default=10, help='interval (sec) to sleep between each experiment')

    args = parser.parse_args()

    dirs: chain[str] = chain(*(glob.glob(path) for path in args.config_dir))

    silent: bool = args.silent
    print_metric_log: bool = args.print_metric_log
    verbose: bool = args.verbose
    interval: int = args.expt_interval

    for i, workspace in enumerate(dirs):
        if i is not 0:
            await asyncio.sleep(interval)

        if not await launch(Path(workspace), silent, print_metric_log and silent, verbose and silent):
            break


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON:
        sys.exit('Python {}.{} or later is required.\n'.format(*MIN_PYTHON))

    asyncio.run(main())
