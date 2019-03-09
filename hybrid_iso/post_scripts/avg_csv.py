#!/usr/bin/env python3
# coding: UTF-8

import csv
from collections import OrderedDict
from pathlib import Path
from statistics import mean
from typing import List, Tuple

from ordered_set import OrderedSet

from benchmon.configs.containers import BenchConfig
from benchmon.configs.parsers import BenchParser
from .tools import WorkloadResult, read_result


def run(workspace: Path, *_):
    bench_configs: Tuple[BenchConfig, ...] = tuple(BenchParser(workspace).parse())
    results: List[WorkloadResult] = read_result(bench_configs)
    output_path = workspace / 'generated'

    output_path.mkdir(parents=True, exist_ok=True)

    fields = tuple(map(lambda x: x.name, results))
    with (output_path / 'avg.csv').open('w') as fp:
        csv_writer = csv.DictWriter(fp, ('category', *fields))
        csv_writer.writeheader()

        runtime_dict = OrderedDict({'category': 'runtime'})
        for workload in results:
            runtime_dict[workload.name] = workload.runtime
        csv_writer.writerow(runtime_dict)

        perf_events: OrderedSet[str] = OrderedSet(results[0].perf.keys())
        for category in perf_events:
            row_dict = OrderedDict({'category': category})

            for workload in results:
                row_dict[workload.name] = mean(workload.perf[category])

            csv_writer.writerow(row_dict)

        resctrl_events: OrderedSet[str] = OrderedSet(results[0].resctrl[0].keys())
        for category in resctrl_events:
            row_dict = OrderedDict({'category': category})

            for workload in results:
                row_dict[workload.name] = sum(mean(resctrl[category]) for resctrl in workload.resctrl)

            csv_writer.writerow(row_dict)
