import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from flux_orm.config import postgresql_connection_settings
from flux_orm.custom_logger import logger

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


config.set_main_option(
    "sqlalchemy.url",
    str(postgresql_connection_settings.migration_async_url) + "?async_fallback=True",
)

from flux_orm.database import Model  # noqa: E402

logger.info(f"Tables found in metadata: {Model.metadata.tables.keys()}")
target_metadata = Model.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        connect_args={"password": os.getenv("DB_PASS")},
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Type tracking
        compare_server_default=True,  # Server default tracking
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        connect_args={"password": os.getenv("DB_PASS")},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Type tracking
            compare_server_default=True,  # Server default tracking
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
