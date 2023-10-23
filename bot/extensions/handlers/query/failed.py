from aiogram.types import InputTextMessageContent, InlineQueryResultArticle, InlineQuery


def get_failed_result(query: InlineQuery, message: str, description: str):
    return InlineQueryResultArticle(
        id=query.query,
        type="article",
        title="Failed",
        input_message_content=InputTextMessageContent(message_text=message),
        description=description,
    )
