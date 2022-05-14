from unittest import mock

from manage import start


def test_start():
    bot = mock.MagicMock()
    start(bot)
