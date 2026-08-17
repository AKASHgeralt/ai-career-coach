import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Make the backend package importable so `database` and `app.*` resolve the
# same way they do when uvicorn runs from this directory.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from database import Base  # noqa: E402

# Importing every model module registers its table on Base.metadata, which is
# what autogenerate diffs against. A model that isn't imported here is invisible
# to migrations.
from app.models import (  # noqa: E402,F401
    user,
    resume,
    skill_gap,
    recommendation,
    interview,
    github,
    roadmap_task,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL lives in .env, never in alembic.ini — keeps credentials out of the
# repo. ALEMBIC_DATABASE_URL allows pointing at a scratch DB when generating a
# from-scratch baseline.
database_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set; cannot run migrations")
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
