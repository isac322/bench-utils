# coding: UTF-8

import platform

from benchmon.utils import linux_version

if platform.system() == 'Linux':
    if linux_version() >= (3, 13):
        # noinspection PyUnresolvedReferences
        from ._platform_depent.power.intel_rapl import PowerMonitor
    else:
        raise NotImplementedError('Only Linux (>= 3.13) based platforms are supported')
else:
    raise NotImplementedError('Only Linux (>= 3.13) based platforms are supported')
