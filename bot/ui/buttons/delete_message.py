from aiogram.types import InlineKeyboardButton

deleteMessageButtonPrefix = "del_msg"

deleteMessageButton = InlineKeyboardButton(
    text="убрать", callback_data=deleteMessageButtonPrefix
)
