from extensions.handlers.message.base import BaseHandler as _BaseHandler

from ._context import ChatGPTContextManager


class BaseHandler(ChatGPTContextManager, _BaseHandler):
    pass
