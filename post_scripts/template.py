#!/usr/bin/env python3
# coding: UTF-8

from pathlib import Path
from typing import List, Tuple

from configs.bench_config import BenchConfig
from configs.launcher_config import LauncherConfig
from configs.perf_config import PerfConfig
from configs.rabbit_mq_config import RabbitMQConfig
from post_scripts.tools import WorkloadResult, read_config, read_result


def run(workspace: Path, global_cfg_path: Path):
    results: List[WorkloadResult] = read_result(workspace)
    output_path = workspace / 'output'

    bench_configs, perf_config, rabbit_config, launcher_config = read_config(workspace, global_cfg_path)
    # type: Tuple[BenchConfig, ...], PerfConfig, RabbitMQConfig, LauncherConfig

    if not output_path.exists():
        output_path.mkdir(parents=True)

    with open(output_path / 'avg.csv', mode='w') as fp:
        fp.flush()
