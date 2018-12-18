#!/usr/bin/env python3
# coding: UTF-8

from pathlib import Path
from typing import List, Tuple

from bench_toolbox.configs.containers import BenchConfig, PerfConfig, RabbitMQConfig
from .tools import WorkloadResult, read_config, read_result
from ..configs.containers.launcher import LauncherConfig


def run(workspace: Path, global_cfg_path: Path):
    results: List[WorkloadResult] = read_result(workspace)
    output_path = workspace / 'output'

    bench_configs, perf_config, rabbit_config, launcher_config = read_config(workspace, global_cfg_path)
    # type: Tuple[BenchConfig, ...], PerfConfig, RabbitMQConfig, LauncherConfig

    if not output_path.exists():
        output_path.mkdir(parents=True)

    with (output_path / 'avg.csv').open('w') as fp:
        fp.flush()
