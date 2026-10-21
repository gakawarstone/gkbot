from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from configs import env
from models import books, gkfeed, road, tasks, timezone, users  # noqa: F401
from models.base import Base

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
            return url.set(drivername=DIALECT_MAP[backend]).render_as_string(
                hide_password=False
            )
        return url.render_as_string(hide_password=False)

    dialect = env.DB_DIALECT
    if dialect is None or dialect not in DIALECT_MAP:
        raise ValueError(f"Unsupported dialect: {dialect}")

    if dialect == "sqlite":
        return f"{DIALECT_MAP[dialect]}:///{env.DB_NAME or ':memory:'}"

    return URL.create(
        drivername=DIALECT_MAP[dialect],
        username=env.DB_USER,
        password=env.DB_PASSWORD,
        host=env.DB_HOST,
        port=int(env.DB_PORT) if env.DB_PORT else None,
        database=env.DB_NAME,
    ).render_as_string(hide_password=False)


engine = create_async_engine(get_database_url())
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def on_shutdown() -> None:
    await engine.dispose()
