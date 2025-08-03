from enum import Enum
from dataclasses import dataclass
from typing import Coroutine, Callable, Sequence


# FIXME: aigram have this type
class ChatType(Enum):
    private = "private"
    group = "group"
    super_group = "supergroup"


@dataclass
class BotConfig:
    token: str
    tasks_on_startup_async: Sequence[Coroutine]
    tasks_on_startup_sync: Sequence[Callable]
    default_commands: dict[str, str]
    parse_mode: str
    admins: list[int]
    api_url: str = "https://api.telegram.org"
