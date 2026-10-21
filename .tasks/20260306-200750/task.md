# Migrate from Tortoise to SQLAlchemy

- STATUS: CLOSED
- PRIORITY: 1

## Plan

1. [x] **Add Dependencies**
   - Add `sqlalchemy[asyncio]`, `alembic`, `aiosqlite`, `aiomysql` to `pyproject.toml`.
   - Install dependencies using `uv`.

2. [x] **Core Database Setup**
   - Define SQLAlchemy `Base` in `bot/models/base.py`.
   - Update `bot/configs/db.py` to support SQLAlchemy `AsyncEngine` and `async_sessionmaker`.
   - Ensure support for SQLite, PostgreSQL, and MySQL as in current Tortoise setup.

3. [x] **Migrate Models**
   - Rewrite the following models in `bot/models/`:
     - `Book`
     - `GkFeed`
     - `PomodoroStats`, `RoadSettings`, `Habits` (in `bot/models/road.py`)
     - `Task`
     - `TimeZone`
     - `Users`
   - Use SQLAlchemy 2.0-style `Mapped` and `mapped_column`.

4. [x] **Update Repositories & Services**
   - Update all classes in `bot/services/repositories/` to use `AsyncSession`.
   - Update `bot/services/timezone.py`, `bot/services/gkfeed_auth.py`, `bot/services/schedule.py`, `bot/services/pomodoro.py`.
   - Update `bot/middlewares/register_user.py`.
   - Migrate Tortoise queries to SQLAlchemy Core/ORM queries.

5. [x] **Integrate with App Lifecycle**
   - Update `bot/configs/startup.py` to initialize SQLAlchemy.
   - Update `bot/handlers/on_shutdown.py` to close connections.
   - Remove Tortoise-related code from `bot/configs/db.py` and elsewhere.

6. [x] **Database Migrations (Alembic)**
   - Initialize Alembic.
   - Configure it to use the new models.
   - Generate initial migration.

7. [x] **Validation & Testing**
   - Update and run tests in `bot/tests/`.
   - Verify functionality manually (RoadSettings tests passed).

8. [x] **Cleanup**
   - Remove `tortoise-orm` from `pyproject.toml`.
   - Update `requirements.txt`.
