import pytest
from sqlalchemy.engine import make_url

from configs import db, env


@pytest.mark.parametrize(
    "backend, driver", [("postgresql", "asyncpg"), ("mysql", "aiomysql")]
)
@pytest.mark.parametrize("use_db_url", [True, False])
def test_database_url_preserves_credentials(
    monkeypatch: pytest.MonkeyPatch, backend: str, driver: str, use_db_url: bool
) -> None:
    password = "secret@:/password"
    monkeypatch.setattr(env, "DB_DIALECT", backend)
    monkeypatch.setattr(env, "DB_USER", "test_user")
    monkeypatch.setattr(env, "DB_PASSWORD", password)
    monkeypatch.setattr(env, "DB_HOST", "localhost")
    monkeypatch.setattr(env, "DB_PORT", "5432")
    monkeypatch.setattr(env, "DB_NAME", "test_db")
    monkeypatch.setattr(
        env,
        "DB_URL",
        f"{backend}://test_user:secret%40%3A%2Fpassword@localhost:5432/test_db"
        if use_db_url
        else None,
    )

    url = make_url(db.get_database_url())

    assert url.drivername == f"{backend}+{driver}"
    assert url.username == "test_user"
    assert url.password == password
    assert url.database == "test_db"
