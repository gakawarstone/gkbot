from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup


class FeedAddedMarkup:
    @staticmethod
    def as_markup(feed_url: str) -> InlineKeyboardMarkup | None:
        """Copy the saved feed URL for reuse in another feed reader."""
        if not 1 <= len(feed_url) <= 256:
            return None

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Копировать URL ленты",
                        copy_text=CopyTextButton(text=feed_url),
                    )
                ]
            ]
        )
