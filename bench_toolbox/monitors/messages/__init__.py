# coding: UTF-8

from typing import TypeVar

from .base_message import BaseMessage

MessageType = TypeVar('MessageType', bound=BaseMessage)
