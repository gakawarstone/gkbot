from dataclasses import dataclass
from sqlalchemy import select
from configs import db
from models.gkfeed import GkFeed


@dataclass
class GkfeedCredentials:
    login: str
    password: str


class GkfeedAuthService:
    async def login(self, user_id: int, login: str, password: str) -> bool:
        """Save user's credentials for GkFeed."""
        async with db.SessionLocal() as session:
            stmt = select(GkFeed).where(GkFeed.user_id == user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
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
            stmt = select(GkFeed).where(GkFeed.user_id == user_id)
            result = await session.execute(stmt)
            raw_credentials = result.scalar_one_or_none()
            
            if raw_credentials is None:
                raise ValueError(f"No GkFeed credentials found for user {user_id}")
            return GkfeedCredentials(raw_credentials.login, raw_credentials.password)
