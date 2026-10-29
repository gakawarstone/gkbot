import pytest

from services.gkfeed import GkfeedAuthService, GkfeedCredentials
from tests.mocks.db import use_db


@pytest.mark.asyncio
@use_db
async def test_login_updates_only_requested_user_credentials() -> None:
    service = GkfeedAuthService()
    assert await service.login(1, "first", "password")
    assert await service.login(2, "second", "other-password")
    assert await service.login(1, "updated", "new-password")

    assert await service.get_credentials(1) == GkfeedCredentials(
        "updated", "new-password"
    )
    assert await service.get_credentials(2) == GkfeedCredentials(
        "second", "other-password"
    )
    with pytest.raises(ValueError, match="No GkFeed credentials"):
        await service.get_credentials(3)
