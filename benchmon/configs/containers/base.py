# coding: UTF-8

from abc import ABCMeta


class BaseConfig(metaclass=ABCMeta):
    """ 모든 설정 컨테이너들의 부모 클래스 """
    pass


class MonitorConfig(BaseConfig):
    """
    :mod:`모니터 <benchmon.monitors.base.BaseMonitor>` 에대한 정보를 담고있으며, 모니터를 생성할 때 쓰이기 위한 컨테이너
    """
    pass


class HandlerConfig(BaseConfig):
    """
    :mod:`핸들러 <benchmon.monitors.messages.handlers.base.BaseHandler>` 에대한 정보를 담고있으며,
    핸들러를 생성할 때 쓰이기 위한 컨테이너
    """
    pass
