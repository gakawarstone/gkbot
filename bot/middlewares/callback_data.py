from collections.abc import Sequence

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import (
    AnswerInlineQuery,
    AnswerWebAppQuery,
    Response,
    SavePreparedInlineMessage,
    TelegramMethod,
)
from aiogram.methods.base import TelegramType
from aiogram.types import InlineKeyboardMarkup


class CallbackDataMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        sources: Sequence[object]
        candidate: object = method
        if isinstance(candidate, AnswerInlineQuery):
            sources = candidate.results
        elif isinstance(candidate, (AnswerWebAppQuery, SavePreparedInlineMessage)):
            sources = [candidate.result]
        else:
            sources = [method]

        for source in sources:
            markup = getattr(source, "reply_markup", None)
            if not isinstance(markup, InlineKeyboardMarkup):
                continue
            for row in markup.inline_keyboard:
                for button in row:
                    if button.callback_data is None:
                        continue
                    size = len(button.callback_data.encode("utf-8"))
                    if not 1 <= size <= 64:
                        raise TelegramBadRequest(
                            method=method,
                            message=f"local validation: callback_data must be 1–64 bytes (got {size})",
                        )
        return await make_request(bot, method)
