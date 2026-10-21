from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import Enum

type StartupHook = Callable[[], Awaitable[None] | None]


# FIXME: aigram have this type
class ChatType(Enum):
    private = "private"
    group = "group"
    super_group = "supergroup"


@dataclass
class BotConfig:
    token: str
    startup_hooks: Sequence[StartupHook]
    default_commands: dict[str, str]
    parse_mode: str
    admins: list[int]
    api_url: str = "https://api.telegram.org"
    polling_tasks_concurrency_limit: int = 10
