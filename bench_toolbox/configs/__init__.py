# coding: UTF-8

import json
from importlib import resources
from pathlib import Path
from typing import Any, Dict


def get_full_path(config_file_name: str) -> Path:
    with resources.path(__package__, config_file_name) as path:
        return path


def validate_and_load(config_path: Path) -> Dict[str, Any]:
    if not config_path.is_file():
        raise FileNotFoundError(
                f'\'{config_path.absolute()}\' does not exist. Please copy a template and modify it')

    with config_path.open() as fp:
        return json.load(fp)
