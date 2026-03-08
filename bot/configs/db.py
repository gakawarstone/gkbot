from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from configs import env
from models.base import Base

# Imports for models to be registered in Base.metadata
import models.users
import models.road
import models.books
import models.timezone
import models.tasks
import models.gkfeed

DIALECT_MAP = {
    "postgres": "postgresql+asyncpg",
    "postgresql": "postgresql+asyncpg",
    "mysql": "mysql+aiomysql",
    "sqlite": "sqlite+aiosqlite",
}


def get_database_url() -> str:
    if env.DB_URL:
        url = make_url(env.DB_URL)
        backend = url.get_backend_name()
        if backend in DIALECT_MAP:
            return str(url.set(drivername=DIALECT_MAP[backend]))
        return str(url)

    dialect = env.DB_DIALECT
    if dialect not in DIALECT_MAP:
        raise ValueError(f"Unsupported dialect: {dialect}")

    if dialect == "sqlite":
        return f"{DIALECT_MAP[dialect]}:///{env.DB_NAME or ':memory:'}"

    return str(
        URL.create(
            drivername=DIALECT_MAP[dialect],
            username=env.DB_USER,
            password=env.DB_PASSWORD,
            host=env.DB_HOST,
            port=int(env.DB_PORT) if env.DB_PORT else None,
            database=env.DB_NAME,
        )
    )


engine = create_async_engine(get_database_url())
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def on_shutdown():
    await engine.dispose()
