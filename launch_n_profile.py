#!/usr/bin/env python3
# coding: UTF-8

import argparse
import asyncio
import glob
import json
import logging
import signal
import sys
from itertools import chain
from pathlib import Path
from typing import Tuple

import bench_toolbox.configs.parser as config_parser
from bench_toolbox.benchmark import Benchmark
from bench_toolbox.monitors.messages.handlers.print_handler import PrintHandler
from bench_toolbox.monitors.rdtsc_monitor import RDTSCMonitor
from bench_toolbox.monitors.runtime_monitor import RuntimeMonitor

MIN_PYTHON = (3, 7)


async def launch(workspace: Path,
                 silent: bool,
                 print_metric_log: bool,
                 verbose: bool) -> bool:
    loop = asyncio.get_event_loop()
    local_config_path = workspace / 'config.json'

    if not local_config_path.is_file():
        raise FileNotFoundError(f'\'{local_config_path}\' does not exists')

    with local_config_path.open() as fp:
        local_config = json.load(fp)

    bench_configs = config_parser.workloads(local_config['workloads'])
    perf_config = config_parser.perf()
    rabbit_mq_config = config_parser.rabbit_mq()

    benches: Tuple[Benchmark, ...] = tuple(
            Benchmark
                .Builder(bench_cfg, workspace, logging.DEBUG if verbose else logging.INFO)
                # .build_monitor(RDTSCMonitor.Builder(200))
                .build_monitor(RuntimeMonitor.Builder())
                .add_handler(PrintHandler())
                .finalize()
            for bench_cfg in bench_configs
    )

    current_tasks: Tuple[asyncio.Task, ...] = tuple()

    def cancel_current_tasks():
        nonlocal current_tasks
        for t in current_tasks:
            t.cancel()

    loop.add_signal_handler(signal.SIGINT, cancel_current_tasks)

    current_tasks = tuple(asyncio.create_task(bench.start_and_pause(silent)) for bench in benches)
    await asyncio.wait(current_tasks)

    for bench in benches:
        bench.resume()

    current_tasks = tuple(asyncio.create_task(bench.monitor()) for bench in benches)
    await asyncio.wait(current_tasks)

    loop.remove_signal_handler(signal.SIGINT)

    return not any(map(lambda f: f.cancelled(), current_tasks))


async def main():
    parser = argparse.ArgumentParser(description='Launch benchmark written in config file.')
    parser.add_argument('config_dir', metavar='PARENT_DIR_OF_CONFIG_FILE', type=str, nargs='+',
                        help='Directory path where the config file (config.template.json) exist. (support wildcard *)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print more detail log')
    parser.add_argument('-S', '--silent', action='store_true', help='Do not print any log to stdin. (override -M)')
    parser.add_argument('-M', '--print-metric-log', action='store_true',
                        help='Print all metric related logs to stdout.')
    parser.add_argument('--expt-interval', type=int, default=10,
                        help='interval (sec) to sleep between each experiment')

    args = parser.parse_args()

    dirs: chain[str] = chain(*(glob.glob(path) for path in args.config_dir))

    silent: bool = args.silent
    print_metric_log: bool = args.print_metric_log
    verbose: bool = args.verbose
    interval: int = args.expt_interval

    for i, workspace in enumerate(dirs):
        if i is not 0:
            await asyncio.sleep(interval)

        if not await launch(Path(workspace), silent, print_metric_log, verbose):
            break


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON:
        sys.exit('Python {}.{} or later is required.\n'.format(*MIN_PYTHON))

    asyncio.run(main())
