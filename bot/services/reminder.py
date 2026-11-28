from collections.abc import Awaitable, Callable
from datetime import datetime

from services.schedule import Schedule, Task


class Reminder:
    @staticmethod
    async def add_remind(
        user_id: int,
        date_time: datetime,
        text: str,
        *,
        deliver: Callable[[int, str], Awaitable[None]],
    ) -> None:
        """Schedule a reminder with a picklable delivery callback."""
        await Schedule.add_task(
            task=Task(func=deliver, args=[user_id, text]),
            time=Schedule.to_local_tz(date_time),
        )
