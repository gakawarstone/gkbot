from aiogram.types import InlineKeyboardButton

from ..download import CallbackIdentifier, VideoDownloadCallbackData

PREFIX = "phbtn"


class PornhubDownloadButtonCallbackData(VideoDownloadCallbackData, prefix=PREFIX):
    ph_video_code: CallbackIdentifier


class PornhubDownloadButtonBuilder:
    @staticmethod
    def build(callback_data: PornhubDownloadButtonCallbackData) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=callback_data.action.label,
            callback_data=callback_data.pack(),
        )
