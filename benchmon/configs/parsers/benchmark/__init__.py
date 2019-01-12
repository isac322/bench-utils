# coding: UTF-8

from .base import BaseBenchParser
from .launchable import LaunchableParser

BaseBenchParser.register_parser(LaunchableParser)
