from typing import Union

from aiogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedGif,
    InlineQueryResultCachedMpeg4Gif,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedSticker,
    InlineQueryResultCachedVideo,
    InlineQueryResultCachedVoice,
    InlineQueryResultContact,
    InlineQueryResultDocument,
    InlineQueryResultGame,
    InlineQueryResultGif,
    InlineQueryResultLocation,
    InlineQueryResultMpeg4Gif,
    InlineQueryResultPhoto,
    InlineQueryResultVenue,
    InlineQueryResultVideo,
    InlineQueryResultVoice,
)

ResultsType = list[
    Union[
        InlineQueryResultCachedAudio,
        InlineQueryResultCachedDocument,
        InlineQueryResultCachedGif,
        InlineQueryResultCachedMpeg4Gif,
        InlineQueryResultCachedPhoto,
        InlineQueryResultCachedSticker,
        InlineQueryResultCachedVideo,
        InlineQueryResultCachedVoice,
        InlineQueryResultArticle,
        InlineQueryResultAudio,
        InlineQueryResultContact,
        InlineQueryResultGame,
        InlineQueryResultDocument,
        InlineQueryResultGif,
        InlineQueryResultLocation,
        InlineQueryResultMpeg4Gif,
        InlineQueryResultPhoto,
        InlineQueryResultVenue,
        InlineQueryResultVideo,
        InlineQueryResultVoice,
    ]
]
