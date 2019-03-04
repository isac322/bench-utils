# coding: UTF-8

import csv
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

from benchmon.configs.containers import BenchConfig
from benchmon.utils.numa_topology import cur_online_sockets


@dataclass(frozen=True)
class WorkloadResult:
    name: str
    runtime: float
    perf: Mapping[str, List[float]]
    resctrl: Tuple[Mapping[str, List[float]], ...]
    power: float


def read_result(bench_configs: Tuple[BenchConfig, ...]) -> List[WorkloadResult]:
    ret: List[WorkloadResult] = list()

    with (bench_configs[0].workspace / 'monitored' / 'runtime.json').open() as fp:
        runtime_result = json.load(fp)

    for cfg in bench_configs:
        monitored = cfg.workspace / 'monitored'

        if not monitored.is_dir():
            raise ValueError('run benchmon first!')

        perf = read_csv(monitored / 'perf' / f'{cfg.identifier}.csv')
        resctrl = tuple(
                read_csv(monitored / 'resctrl' / f'{socket_id}_{cfg.identifier}.csv')
                for socket_id in cur_online_sockets()
        )

        ret.append(WorkloadResult(cfg.identifier, runtime_result[cfg.identifier], perf, resctrl, 0))

    return ret


def read_csv(file_path: Path) -> Dict[str, List[float]]:
    ret: OrderedDict[str, List[float]] = OrderedDict()

    with file_path.open() as fp:
        reader = csv.DictReader(fp)

        for field in reader.fieldnames:
            ret[field] = []

        for row in reader:
            for k, v in row.items():  # type: str, str
                ret[k].append(float(v))

    return ret
