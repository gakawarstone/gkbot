import pytest

from services.video import start_timestamp


@pytest.mark.parametrize(
    "value",
    [True, -1, float("nan"), float("inf"), 2**10000, 100],
)
def test_invalid_start_times_are_omitted(value: object) -> None:
    assert start_timestamp(value, 100) is None
