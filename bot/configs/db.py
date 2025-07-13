from tortoise import Tortoise

from . import env

MODELS = [
    "models.users",
    "models.road",
    "models.books",
    "models.timezone",
    "models.tasks",
]


async def on_startup():
    if env.DB_URL:
        await Tortoise.init(db_url=env.DB_URL, modules={"models": MODELS})
    else:
        config = build_db_config_from_env(MODELS)
        await Tortoise.init(config=config)

    await Tortoise.generate_schemas(safe=True)


def build_db_config_from_env(schemas: list[str]) -> dict:
    dialect = env.DB_DIALECT
    user = env.DB_USER
    password = env.DB_PASSWORD
    host = env.DB_HOST
    port = env.DB_PORT
    db_name = env.DB_NAME

    if dialect == "sqlite":
        # SQLite использует file как credential
        credentials = {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": db_name or ":memory:",
            },
        }
    else:
        # PostgreSQL или MySQL
        engine_map = {
            "postgres": "tortoise.backends.asyncpg",
            "postgresql": "tortoise.backends.asyncpg",
            "mysql": "tortoise.backends.mysql",
        }

        if dialect not in engine_map:
            raise ValueError(f"Unsupported dialect: {dialect}")

        credentials = {
            "engine": engine_map[dialect],
            "credentials": {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": db_name,
            },
        }

    return {
        "connections": {
            "default": credentials,
        },
        "apps": {
            "models": {
                "models": schemas,
                "default_connection": "default",
            }
        },
    }
  