"""Alembic environment: usa $DATABASE_URL y el metadata de los modelos de Ratchet."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import create_engine, pool

from ratchet.persistence.models import Base

target_metadata = Base.metadata


def _url() -> str:
    url = os.environ.get("DATABASE_URL") or context.config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL no está seteada (ni sqlalchemy.url en alembic.ini)")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
