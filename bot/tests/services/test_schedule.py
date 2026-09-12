import asyncio
from datetime import datetime, timezone, timedelta

import pytest
from models.tasks import Task as TaskModel
from services.schedule import Schedule, Task
from tests.mocks.db import use_db


_probe_results: list[str] = []


class TaskProbe:
    def __init__(self, name: str, exc: Exception | None = None) -> None:
        self.name = name
        self.exc = exc

    async def __call__(self) -> None:
        _probe_results.append(self.name)
        if self.exc is not None:
            raise self.exc


@pytest.fixture(autouse=True)
def reset_schedule_state():
    _probe_results.clear()
    Schedule._Schedule__attempts.clear()  # type: ignore[attr-defined]
    yield
    Schedule._Schedule__attempts.clear()  # type: ignore[attr-defined]


async def add_due_task(probe: TaskProbe) -> None:
    due = Schedule.to_local_tz(datetime.now() - timedelta(minutes=1))
    await Schedule.add_task(Task(probe), due)


def count_calls(name: str) -> int:
    return _probe_results.count(name)


@pytest.mark.asyncio
@use_db
async def test_successful_task_is_removed_after_run():
    await add_due_task(TaskProbe("ok"))

    await Schedule._Schedule__run_due_tasks()  # type: ignore[attr-defined]

    assert count_calls("ok") == 1
    assert await TaskModel.all().count() == 0


@pytest.mark.asyncio
@use_db
async def test_failed_task_does_not_block_other_tasks():
    await add_due_task(TaskProbe("failing", RuntimeError("boom")))
    await add_due_task(TaskProbe("succeeding"))

    await Schedule._Schedule__run_due_tasks()  # type: ignore[attr-defined]

    assert count_calls("succeeding") == 1
    assert count_calls("failing") == 1
    stored = await TaskModel.all().count()
    assert stored == 1


@pytest.mark.asyncio
@use_db
async def test_failed_task_is_removed_after_max_attempts():
    await add_due_task(TaskProbe("failing", RuntimeError("boom")))

    for _ in range(Schedule._Schedule__max_task_attempts):  # type: ignore[attr-defined]
        await Schedule._Schedule__run_due_tasks()  # type: ignore[attr-defined]

    assert count_calls("failing") == Schedule._Schedule__max_task_attempts  # type: ignore[attr-defined]
    assert await TaskModel.all().count() == 0
    assert Schedule._Schedule__attempts == {}  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_dispatcher_survives_storage_failure(caplog):
    class ExplodingStorage:
        async def get_all(self):
            raise RuntimeError("storage failure")

    original = Schedule._Schedule__tasks  # type: ignore[attr-defined]
    Schedule._Schedule__tasks = ExplodingStorage()  # type: ignore[attr-defined]
    try:
        with caplog.at_level("ERROR"):
            await Schedule.on_startup()
            task = Schedule._Schedule__dispatcher_task  # type: ignore[attr-defined]
            assert task is not None
            await asyncio.sleep(0.01)
            assert not task.done()
            assert "Scheduled tasks pass failed" in caplog.text
    finally:
        await Schedule.on_shutdown()
        Schedule._Schedule__tasks = original  # type: ignore[attr-defined]


@pytest.mark.asyncio
@use_db
async def test_on_shutdown_cancels_dispatcher():
    await Schedule.on_startup()
    task = Schedule._Schedule__dispatcher_task  # type: ignore[attr-defined]
    assert task is not None
    assert not task.done()

    await Schedule.on_shutdown()

    assert task.cancelled()
    assert Schedule._Schedule__dispatcher_task is None  # type: ignore[attr-defined]


class TestScheduleTimezone:
    def test_get_local_tz_returns_timezone(self):
        local_tz = Schedule.get_local_tz()
        assert isinstance(local_tz, timezone)

    def test_to_local_tz_preserves_instant(self):
        """Ensure to_local_tz preserves the same instant in time."""
        utc_time = datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc)
        local_time = Schedule.to_local_tz(utc_time)

        # The timestamp should be the same (same instant in time)
        assert utc_time.timestamp() == local_time.timestamp()

    def test_to_local_tz_converts_naive_datetime(self):
        """Naive datetimes are converted using local timezone assumption."""
        naive_time = datetime(2026, 2, 6, 12, 0, 0)
        local_time = Schedule.to_local_tz(naive_time)

        assert local_time.tzinfo == Schedule.get_local_tz()

    def test_to_local_tz_converts_different_timezone(self):
        """Ensure datetimes from different timezones are converted."""
        # Create a time in UTC+5
        tz_plus_5 = timezone(timedelta(hours=5))
        original_time = datetime(2026, 2, 6, 17, 0, 0, tzinfo=tz_plus_5)

        local_time = Schedule.to_local_tz(original_time)

        # The instant should be preserved
        assert original_time.timestamp() == local_time.timestamp()
        # The timezone should be local
        assert local_time.tzinfo == Schedule.get_local_tz()
