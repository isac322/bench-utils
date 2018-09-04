# coding: UTF-8

from typing import Optional

from .base_handler import BaseHandler
from ..base_message import BaseMessage


class PrintHandler(BaseHandler):
    async def on_message(self, message: BaseMessage) -> Optional[BaseMessage]:
        print({'data': message.data, 'src': message.source.__class__.__name__})
        return message
