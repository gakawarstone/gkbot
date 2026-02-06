from datetime import datetime, timezone, timedelta

from services.schedule import Schedule


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
