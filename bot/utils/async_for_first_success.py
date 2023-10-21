def async_for_first_success(
    sources: list,
    inject_as: str,
    exception_if_all_failed: Exception,
    exception_if_all_failed_inject_args: list[int] = [],
    exception_to_continue: Exception = Exception,
):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for source in sources:
                kwargs[inject_as] = source
                try:
                    return await func(*args, **kwargs)
                except exception_to_continue:
                    continue
            raise exception_if_all_failed(
                *(args[i] for i in exception_if_all_failed_inject_args)
            )

        return wrapper

    return decorator
