from typing import Awaitable, Callable, Dict, Any

from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from models.users import Users
from settings import Session


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
            self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message, data: Dict[str, Any]) -> Any:
        with Session.begin() as session:
            if not session.query(Users).filter_by(
                    user_id=event.from_user.id).first():
                user = Users(
                    user_id=event.from_user.id,
                    user_name=event.from_user.full_name
                )
                session.add(user)
        await handler(event, data)
