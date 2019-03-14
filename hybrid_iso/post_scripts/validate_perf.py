#!/usr/bin/env python3
# coding: UTF-8

import sys
from pathlib import Path
from typing import List, Tuple

from benchmon.configs.containers import BenchConfig
from benchmon.configs.parsers import BenchParser
from .tools import WorkloadResult, read_result


def run(workspace: Path, global_cfg_path: Path):
    bench_configs: Tuple[BenchConfig, ...] = tuple(BenchParser(workspace).parse())
    results: List[WorkloadResult] = read_result(bench_configs)

    error_file = workspace / 'ERROR'
    if error_file.exists():
        error_file.unlink()

    for result in results:
        if 0 in result.perf.get('llc_occupancy'):
            print(f'{result.name} has 0 llc_occupancy value!', file=sys.stderr)

            if not error_file.exists():
                with error_file.open('w') as fp:
                    fp.write(result.name)
            else:
                with error_file.open('a') as fp:
                    fp.write(result.name)
