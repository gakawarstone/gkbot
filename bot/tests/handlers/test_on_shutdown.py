from unittest.mock import AsyncMock, patch

from handlers.on_shutdown import on_shutdown


async def test_shutdown_stops_schedule_before_disposing_database() -> None:
    events: list[str] = []

    async def stop_schedule() -> None:
        events.append("schedule")

    async def dispose_database() -> None:
        events.append("database")

    with (
        patch(
            "handlers.on_shutdown.Schedule.on_shutdown",
            AsyncMock(side_effect=stop_schedule),
        ),
        patch(
            "handlers.on_shutdown.db.on_shutdown",
            AsyncMock(side_effect=dispose_database),
        ),
    ):
        await on_shutdown()

    assert events == ["schedule", "database"]
