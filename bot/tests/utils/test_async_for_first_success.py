import pytest

from utils.async_for_first_success import async_for_first_success


@pytest.mark.parametrize("unexpected", [False, True])
async def test_only_configured_failures_try_another_source(unexpected: bool) -> None:
    calls: list[int] = []

    @async_for_first_success(
        [1, 2], "source", LookupError, exception_to_continue=ValueError
    )
    async def fetch(*, source: int) -> int:
        calls.append(source)
        if unexpected:
            raise RuntimeError("unexpected failure")
        if source == 1:
            raise ValueError("try next source")
        return source

    if unexpected:
        with pytest.raises(RuntimeError, match="unexpected failure"):
            await fetch()
        assert calls == [1]
    else:
        assert await fetch() == 2
        assert calls == [1, 2]


async def test_exhausted_sources_include_requested_arguments() -> None:
    @async_for_first_success([1], "source", LookupError, [0], ValueError)
    async def fetch(url: str, *, source: int) -> None:
        raise ValueError("source unavailable")

    with pytest.raises(LookupError) as raised:
        await fetch("https://example.invalid")
    assert raised.value.args == ("https://example.invalid",)
