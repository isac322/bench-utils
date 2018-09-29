# coding: UTF-8

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import BaseHandler

if TYPE_CHECKING:
    from ..base import MonitoredMessage


class PrintHandler(BaseHandler):
    async def on_message(self, message: MonitoredMessage) -> Optional[MonitoredMessage]:
        print({'data': message.data, 'src': message.source.__class__.__name__})
        return message
