import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from models import SQLModel

# --- Alembic config ---
config = context.config
fileConfig(config.config_file_name)

# --- DB URL из окружения ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# --- Метаданные моделей ---
target_metadata = SQLModel.metadata


# --- ✅ Регистрируем кастомный рендер-хук ДО всего остального ---
from alembic.autogenerate import renderers
import sqlmodel


@renderers.dispatch_for(sqlmodel.sql.sqltypes.AutoString)
def render_auto_string(type_, autogen_context):
    """Позволяет Alembic автоматически добавлять импорт sqlmodel и правильно сериализовать тип."""
    autogen_context.imports.add("import sqlmodel")
    return "sqlmodel.sql.sqltypes.AutoString()"


# --- Основные функции Alembic ---
def run_migrations_offline():
    """Запуск миграций без подключения к БД."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Запуск миграций с подключением к БД."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# --- Точка входа ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
