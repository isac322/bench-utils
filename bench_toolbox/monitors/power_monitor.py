# coding: UTF-8

import platform

if platform.system() == 'Linux':
    # TODO: check linux kernel version (only >= 3.13)
    # noinspection PyUnresolvedReferences
    from .platform_depent.power_monitor.intel_rapl import PowerMonitor
else:
    raise NotImplementedError('Only Linux (>= 3.13) based platforms are supported')
