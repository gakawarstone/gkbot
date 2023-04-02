from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey


fake_state = FSMContext(
    bot=AsyncMock(),
    storage=MemoryStorage(),
    key=StorageKey(
        bot_id=1,
        chat_id=2,
        user_id=3
    )
)
