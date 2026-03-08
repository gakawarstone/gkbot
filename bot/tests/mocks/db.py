from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models.base import Base
from configs.db import SessionLocal, engine as _engine

# Ensure models are imported
import models.users
import models.road
import models.books
import models.timezone
import models.tasks
import models.gkfeed

def use_db(func):
    async def wrapper(*args, **kwargs):
        # We can use the existing engine if it's sqlite :memory: or create a new one for test
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
        
        # Override SessionLocal in configs.db for the duration of the test?
        # That's tricky without dependency injection.
        # But many services use configs.db.SessionLocal.
        
        # For now, let's just use the global engine if it's configured for sqlite memory, 
        # or create schemas on it.
        
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Mock SessionLocal
        import configs.db
        original_session_local = configs.db.SessionLocal
        configs.db.SessionLocal = TestSessionLocal

        try:
            result = await func(*args, **kwargs)
        finally:
            await test_engine.dispose()
            configs.db.SessionLocal = original_session_local

        return result

    return wrapper
