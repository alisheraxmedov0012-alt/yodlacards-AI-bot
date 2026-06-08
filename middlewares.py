from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any

import time


users = {}


class AntiSpamMiddleware(BaseMiddleware):

    async def __call__( self, handler: Callable, event: Message, data: Dict[str, Any] ):

        user_id = event.from_user.id

        now = time.time()

        if user_id in users:

            if now - users[user_id] < 1:

                return

        users[user_id] = now

        return await handler(event, data)
