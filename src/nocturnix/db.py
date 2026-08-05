from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command  # type: ignore[attr-defined]
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm.session import Session


class Base(DeclarativeBase):
    pass


def safe_database_provider(database_url: str) -> str:
    url = make_url(database_url)
    return url.get_backend_name()


def ensure_sqlite_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:"):
        Path(str(url.database)).parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str, echo: bool = False) -> Engine:
    ensure_sqlite_parent(database_url)
    connect_args: dict[str, Any] = {}
    if safe_database_provider(database_url) == "sqlite":
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, echo=echo, future=True, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def alembic_config(database_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def run_migrations(database_url: str) -> None:
    ensure_sqlite_parent(database_url)
    command.upgrade(alembic_config(database_url), "head")


def current_revision(database_url: str) -> str | None:
    engine: Engine | None = None

    try:
        engine = create_database_engine(database_url)
        with engine.connect() as conn:
            if not engine.dialect.has_table(conn, "alembic_version"):
                return None
            return conn.execute(
                text("select version_num from alembic_version")
            ).scalar_one_or_none()
    finally:
        if engine is not None:
            engine.dispose()


def head_revision() -> str:
    return str(ScriptDirectory.from_config(alembic_config("sqlite:///:memory:")).get_current_head())


def database_ready(database_url: str) -> bool:
    engine: Engine | None = None

    try:
        engine = create_database_engine(database_url)

        with engine.connect() as conn:
            conn.execute(text("select 1"))

        return current_revision(database_url) == head_revision()

    except Exception:
        return False

    finally:
        if engine is not None:
            engine.dispose()
