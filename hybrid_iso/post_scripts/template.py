#!/usr/bin/env python3
# coding: UTF-8

from pathlib import Path
from typing import List, Tuple

from benchmon.configs.containers import BenchConfig, PerfConfig, PrivilegeConfig, RabbitMQConfig
from benchmon.configs.parsers import BenchParser
from .tools import WorkloadResult, read_result
from ..configs.containers import LauncherConfig


def run(workspace: Path, privilege_config: PrivilegeConfig, launcher_config: LauncherConfig,
        perf_config: PerfConfig, rabbit_mq_config: RabbitMQConfig):
    bench_configs: Tuple[BenchConfig, ...] = tuple(BenchParser(workspace).parse())
    results: List[WorkloadResult] = read_result(bench_configs)
    output_path = workspace / 'generated'

    output_path.mkdir(parents=True, exist_ok=True)

    with (output_path / 'avg.csv').open('w') as fp:
        fp.flush()
