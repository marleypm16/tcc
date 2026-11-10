"""Ambiente do Alembic: usa a URL da configuração do Lastro e os metadados dos modelos ORM."""

from alembic import context
from sqlalchemy import engine_from_config, pool

from lastro.config import obter_configuracao
from lastro.persistencia.modelos import Base

config = context.config
config.set_main_option("sqlalchemy.url", obter_configuracao().database_url)
target_metadata = Base.metadata


def executar_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def executar_online() -> None:
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as conexao:
        context.configure(connection=conexao, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    executar_offline()
else:
    executar_online()
