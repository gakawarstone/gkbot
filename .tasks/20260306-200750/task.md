# Migrate from Tortoise to SQLAlchemy

Status: closed.

Required decisions:
- Use SQLAlchemy 2.0 `Mapped` models and async sessions, with Alembic migrations.
- Preserve SQLite, PostgreSQL and MySQL support.
- Preserve existing persistence behavior and application startup/shutdown cleanup.
