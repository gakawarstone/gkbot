from configs import db
from models.gkfeed import GkFeed

from ._types import GkfeedCredentials


class GkfeedAuthService:
    async def login(self, user_id: int, login: str, password: str) -> bool:
        """Save user's credentials for GkFeed."""
        async with db.SessionLocal() as session:
            existing = await session.get(GkFeed, user_id)

            if existing:
                existing.login = login
                existing.password = password
            else:
                new_feed = GkFeed(user_id=user_id, login=login, password=password)
                session.add(new_feed)
            await session.commit()
        return True

    async def get_credentials(self, user_id: int) -> GkfeedCredentials:
        """Get user's credentials for GkFeed."""
        async with db.SessionLocal() as session:
            raw_credentials = await session.get(GkFeed, user_id)

            if raw_credentials is None:
                raise ValueError(f"No GkFeed credentials found for user {user_id}")
            return GkfeedCredentials(raw_credentials.login, raw_credentials.password)
