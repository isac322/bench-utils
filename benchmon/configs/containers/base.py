# coding: UTF-8

from abc import ABCMeta


class BaseConfig(metaclass=ABCMeta):
    pass


class MonitorConfig(BaseConfig):
    pass


class HandlerConfig(BaseConfig):
    pass
