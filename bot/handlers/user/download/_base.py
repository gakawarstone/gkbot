from contrib.handlers.message.base import BaseHandler as _BaseHandler

from ._context import DownloadContextManager


class BaseHandler(DownloadContextManager, _BaseHandler):
    pass
