# coding: UTF-8

"""
:mod:`utils` -- 부수적으로 필요한 기능들
=========================================================

다른 모듈들에서 공통적으로 사용하는 기능들을 모아놓은 모듈.

OS API의 wrapper등이 있다.

.. module:: benchmon.utils
    :synopsis: 부수적으로 필요한 기능들
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

import re
import subprocess
from typing import Tuple

from .resctrl import ResCtrl

_linux_version_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+).*')


def linux_version() -> Tuple[int, int, int]:
    output: str = subprocess.check_output(['uname', '-r'], encoding='UTF-8')
    matched = _linux_version_pattern.search(output)
    groups = matched.groups()
    # noinspection PyTypeChecker
    return tuple(map(int, groups))
