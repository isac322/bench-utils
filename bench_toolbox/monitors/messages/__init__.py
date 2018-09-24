# coding: UTF-8

from typing import TypeVar

from .base_message import BaseMessage, GeneratedMessage, MonitoredMessage

MessageType = TypeVar('MessageType', bound=BaseMessage)
