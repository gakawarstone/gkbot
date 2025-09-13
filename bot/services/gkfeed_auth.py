from dataclasses import dataclass

from models.gkfeed import GkFeed


@dataclass
class GkfeedCredentials:
    login: str
    password: str


class GkfeedAuthService:
    async def login(self, user_id: int, login: str, password: str) -> bool:
        """Save user's credentials for GkFeed."""
        await GkFeed.update_or_create(
            defaults={"login": login, "password": password},
            user_id=user_id,
        )
        return True

    async def get_credentials(self, user_id: int) -> GkfeedCredentials:
        """Get user's credentials for GkFeed."""
        raw_credentials = await GkFeed.get_or_none(user_id=user_id)
        if raw_credentials is None:
            raise ValueError(f"No GkFeed credentials found for user {user_id}")
        return GkfeedCredentials(raw_credentials.login, raw_credentials.password)
