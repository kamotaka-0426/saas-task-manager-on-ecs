import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Make the repo root importable so `app.*` imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings  # noqa: E402
from app.core.base import Base  # noqa: E402

# Register all models so Base.metadata is populated for autogenerate
import app.models.user  # noqa: F401, E402
import app.models.organization  # noqa: F401, E402
import app.models.project  # noqa: F401, E402
import app.models.issue  # noqa: F401, E402
import app.models.comment  # noqa: F401, E402
import app.models.activity_log  # noqa: F401, E402
import app.models.label  # noqa: F401, E402

config = context.config
# Override sqlalchemy.url from settings (reads env vars)
# configparser interprets % as interpolation syntax, so escape % → %%
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
