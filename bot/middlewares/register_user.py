import aiogram
from .base import BaseMiddleware

from models.users import Users
from settings import Session


class RegisterUserMiddleware(BaseMiddleware):
    # async def on_pre_process_message(self, message: aiogram.types.Message,
    #                                  data: dict):
    #     with Session.begin() as session:
    #         if session.query(Users).filter_by(
    #                 user_id=message.from_user.id).first():
    #             return
    #         user = Users(
    #             user_id=message.from_user.id,
    #             user_name=message.from_user.full_name
    #         )
    #         session.add(user)

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]) -> Any:

        await handler(event, data)
