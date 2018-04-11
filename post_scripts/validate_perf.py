#!/usr/bin/env python3
# coding: UTF-8

import sys
from pathlib import Path
from typing import List

from post_scripts.tools import WorkloadResult, read_result


def run(workspace: Path, global_cfg_path: Path):
    results: List[WorkloadResult] = read_result(workspace)
    output_path = workspace / 'output'

    if not output_path.exists():
        output_path.mkdir(parents=True)

    error_file = output_path / 'ERROR'
    if error_file.exists():
        error_file.unlink()

    for result in results:
        if 0 in result.metrics.get('llc_occupancy'):
            print(f'{result.name} has 0 llc_occupancy value!', file=sys.stderr)

            if not error_file.exists():
                with open(error_file, mode='w') as fp:
                    fp.write(result.name)
            else:
                with open(error_file, mode='a') as fp:
                    fp.write(result.name)
