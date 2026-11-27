from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramServerError,
)
from aiohttp import ClientConnectionError, ClientPayloadError, ClientResponseError

from services.http import HttpRequestError
from services.matreshka import InvalidMatreshkaVideoUrl, MatreshkaVideoUnavailable
from services.tiktok.exceptions import (
    TikTokInfoExtractionFailed,
    TikTokInvalidUrl,
    TikTokVideoUrlExtractionFailed,
)
from services.youtube import UnavailableVideo


class FeedMediaExtractionError(ValueError):
    """Expected missing or malformed media in external feed content."""


# Do not add generic ValueError/TypeError/KeyError or TelegramAPIError here.
# Those also represent programming, authorization and rate-limit failures.
RECOVERABLE_FEED_ERRORS = (
    FeedMediaExtractionError,
    HttpRequestError,
    ClientConnectionError,
    ClientPayloadError,
    ClientResponseError,
    TimeoutError,
    InvalidMatreshkaVideoUrl,
    MatreshkaVideoUnavailable,
    TikTokInfoExtractionFailed,
    TikTokInvalidUrl,
    TikTokVideoUrlExtractionFailed,
    UnavailableVideo,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramServerError,
)
