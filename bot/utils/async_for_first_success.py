from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any


def async_for_first_success(
    sources: list[Any],
    inject_as: str,
    exception_if_all_failed: type[Exception],
    exception_if_all_failed_inject_args: list[int] | None = None,
    exception_to_continue: type[Exception] = Exception,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    argument_indexes = tuple(exception_if_all_failed_inject_args or ())

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for source in sources:
                kwargs[inject_as] = source
                try:
                    return await func(*args, **kwargs)
                except exception_to_continue:
                    continue
            raise exception_if_all_failed(*(args[i] for i in argument_indexes))

        return wrapper

    return decorator
