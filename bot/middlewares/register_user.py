from typing import Awaitable, Callable, Dict, Any
from sqlalchemy import select
from aiogram.types import User
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

from configs import db
from models.users import Users


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = getattr(event, "from_user", None)
        if not user:
            raise ValueError("Event does not contain a user")

        async with db.SessionLocal() as session:
            stmt = select(Users).where(Users.user_id == user.id)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                new_user = Users(
                    user_id=user.id, user_name=getattr(user, "full_name", "")
                )
                session.add(new_user)
                await session.commit()

        await handler(event, data)
