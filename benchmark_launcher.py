#!/usr/bin/env python3
# coding: UTF-8

import argparse
import asyncio
import contextlib
import importlib
import json
import signal
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, Union

from benchmark.benchmark import Benchmark
from configs.bench_config import BenchConfig
from configs.launcher_config import LauncherConfig
from configs.perf_config import PerfConfig, PerfEvent
from configs.rabbit_mq_config import RabbitMQConfig


def parse_workload_cfg(wl_configs: List[Dict[str, Any]]) -> Tuple[BenchConfig, ...]:
    return tuple(
            BenchConfig(config['name'],
                        config['num_of_threads'],
                        config['binding_cores'],
                        config['numa_nodes'],
                        config['cpu_freq'])
            for config in wl_configs
    )


def parse_perf_cfg(global_cfg: Dict[str, Any], local_cfg: Dict[str, Any]) -> PerfConfig:
    events = tuple(
            PerfEvent(elem, elem)
            if type(elem) is str else
            PerfEvent(elem['event'], elem['alias'])
            for elem in global_cfg['events'] + local_cfg['extra_events']
    )

    return PerfConfig(global_cfg['interval'], events)


def parse_rabbit_mq_cfg(rabbit_cfg: Dict[str, Any]) -> RabbitMQConfig:
    return RabbitMQConfig(rabbit_cfg['host'], rabbit_cfg['queue_name']['workload_creation'])


def parse_launcher_cfg(launcher_cfg: Dict[str, Union[bool, List[str]]]) -> LauncherConfig:
    cwd = Path(__file__).parent
    post_scripts = cwd / 'post_scripts'

    if not post_scripts.exists():
        post_scripts.mkdir()

    postscripts: List[Path] = []

    for script in launcher_cfg.get('post_scripts', []):
        script_path = post_scripts / script

        if not script_path.exists():
            raise FileNotFoundError(f'post script {script_path} is not exist')
        elif not script_path.is_file():
            raise ValueError(f'post script {script_path} is not a file')

        postscripts.append(script_path)

    return LauncherConfig(postscripts,
                          launcher_cfg.get('hyper-threading', False),
                          launcher_cfg.get('stops_with_the_first', False))


def create_benchmarks(bench_cfgs: Tuple[BenchConfig, ...],
                      perf_cfg: PerfConfig,
                      rabbit_cfg: RabbitMQConfig,
                      work_space: Path) -> Generator[Benchmark, Any, None]:
    bench_dict: Dict[str, List[BenchConfig]] = dict()

    for bench in bench_cfgs:
        if bench.name not in bench_dict:
            bench_dict[bench.name] = []
        bench_dict[bench.name].append(bench)

    return (
        Benchmark(BenchConfig.gen_identifier(bench_cfg, bench_dict[bench_cfg.name]),
                  bench_cfg, perf_cfg, rabbit_cfg, work_space)
        for bench_cfg in bench_cfgs
    )


_ENERGY_FILE_NAME = 'energy_uj'


@contextlib.contextmanager
def power_monitor(work_space: Path):
    base_dir = Path('/sys/class/powercap/intel-rapl')

    monitors: Dict[Path, Tuple[int, Dict[Path, int]]] = dict()

    while True:
        socket_id = len(monitors)
        socket_monitor = base_dir / f'intel-rapl:{socket_id}'

        if socket_monitor.exists():
            with open(socket_monitor / _ENERGY_FILE_NAME) as fp:
                socket_power = int(fp.readline())

            socket_dict: Dict[Path, int] = {}
            monitors[socket_monitor] = (socket_power, socket_dict)

            while True:
                sub_id = len(socket_dict)
                sub_monitor = socket_monitor / f'intel-rapl:{socket_id}:{sub_id}'

                if sub_monitor.exists():
                    with open(sub_monitor / _ENERGY_FILE_NAME) as fp:
                        before = int(fp.readline())
                        socket_dict[sub_monitor] = before
                else:
                    break
        else:
            break

    yield

    ret: List[Dict[str, Union[str, List[Dict[str, int]]]]] = list()

    for socket_path, (prev_socket_power, socket) in monitors.items():
        with open(socket_path / 'name') as name_fp, open(socket_path / _ENERGY_FILE_NAME) as power_fp:
            sub_name = name_fp.readline().strip()
            after = int(power_fp.readline())

        ret_dict: Dict[str, Union[str, List[Dict[str, int]]]] = {
            'package_name': sub_name,
            'power': after - prev_socket_power,
            'domains': dict()
        }

        for path, before in socket.items():
            with open(path / _ENERGY_FILE_NAME) as energy_fp, open(path / 'name') as name_fp:
                after = int(energy_fp.readline())
                name = name_fp.readline().strip()

                ret_dict['domains'][name] = after - before

        ret.append(ret_dict)

    result_file = work_space / 'result.json'
    if result_file.exists():
        with open(result_file, mode='r+') as fp:
            try:
                original = json.load(fp)
                original['power'] = ret

                fp.seek(0)
                json.dump(original, fp, indent=4)

            except json.decoder.JSONDecodeError:
                fp.seek(0)
                fp.truncate()
                json.dump({'power': ret}, fp, indent=4)
    else:
        with open(result_file, mode='w') as fp:
            json.dump({'power': ret}, fp, indent=4)


# TODO
def set_hyper_threading(flag: bool):
    pass


GLOBAL_CFG_PATH = Path(__file__).absolute().parent.parent / 'config.json'


def launch(loop: asyncio.AbstractEventLoop, workspace: Path, no_log: bool, no_metric_log: bool):
    result_file = workspace / 'result.json'
    if result_file.exists():
        result_file.unlink()

    with open(workspace / 'config.json') as local_config_fp, \
            open(GLOBAL_CFG_PATH) as global_config_fp:
        local_cfg_source: Dict[str, Any] = json.load(local_config_fp)
        global_cfg_source: Dict[str, Any] = json.load(global_config_fp)

        bench_cfges = parse_workload_cfg(local_cfg_source['workloads'])
        perf_cfg = parse_perf_cfg(global_cfg_source['perf'], local_cfg_source['perf'])
        rabbit_cfg = parse_rabbit_mq_cfg(global_cfg_source['rabbitMQ'])
        launcher_cfg = parse_launcher_cfg(local_cfg_source['launcher'])

    task_map: Dict[asyncio.Task, Benchmark] = dict()

    def stop_all(_=None):
        # FIXME: logging
        print('stopping all benchmarks...')
        for a_task, a_bench in task_map.items():
            if not a_task.done() and a_bench.is_running:
                a_bench.stop()
            a_task.remove_done_callback(stop_all)

    def store_runtime(a_task: asyncio.Task):
        a_bench = task_map[a_task]

        if result_file.exists():
            with open(result_file, mode='r+') as fp:
                try:
                    original: Dict[str, Any] = json.load(fp)

                    if 'runtime' in original:
                        original['runtime'][a_bench.identifier] = a_bench.runtime
                    else:
                        original['runtime'] = {a_bench.identifier: a_bench.runtime}

                    fp.seek(0)
                    json.dump(original, fp, indent=4)

                except json.decoder.JSONDecodeError:
                    fp.seek(0)
                    fp.truncate()
                    json.dump({'runtime': {a_bench.identifier: a_bench.runtime}}, fp, indent=4)
        else:
            with open(result_file, mode='w') as fp:
                json.dump({'runtime': {a_bench.identifier: a_bench.runtime}}, fp, indent=4)

        a_task.remove_done_callback(store_runtime)

    for bench in create_benchmarks(bench_cfges, perf_cfg, rabbit_cfg, workspace):
        task: asyncio.Task = loop.create_task(bench.create_and_run(no_metric_log))
        if launcher_cfg.stops_with_the_first:
            task.add_done_callback(stop_all)
        task.add_done_callback(store_runtime)
        task_map[task] = bench

    loop.add_signal_handler(signal.SIGHUP, stop_all)
    loop.add_signal_handler(signal.SIGTERM, stop_all)
    loop.add_signal_handler(signal.SIGINT, stop_all)

    with power_monitor(workspace):
        loop.run_until_complete(asyncio.wait(task_map.keys()))

    loop.remove_signal_handler(signal.SIGHUP)
    loop.remove_signal_handler(signal.SIGTERM)
    loop.remove_signal_handler(signal.SIGINT)

    for script in launcher_cfg.post_scripts:
        name = str(script)
        if name.endswith('.py'):
            name = name[:-3]
        script_module = importlib.import_module(name.replace('/', '.'))
        script_module.run(workspace, GLOBAL_CFG_PATH)


def main():
    parser = argparse.ArgumentParser(description='Launch benchmark written in config file.')
    parser.add_argument('config_dir', metavar='PARENT_DIR_OF_CONFIG_FILE', type=str, nargs='+',
                        help='Directory path where the config file (config.json) exist')
    parser.add_argument('-L', '--no-log', action='store_true', help='Do not print any log to stdout. (implies -M)')
    parser.add_argument('-M', '--no-metric-log', action='store_true',
                        help='Do not print any metric related log to stdout.')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    no_log = args.no_log
    no_metric_log = args.no_metric_log

    for workspace in args.config_dir:
        launch(loop, Path(workspace), no_log, no_metric_log)

    loop.close()


if __name__ == '__main__':
    main()
