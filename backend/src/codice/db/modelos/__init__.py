"""Modelos ORM das tabelas (docs/arquitetura-tcc.md, seção 7).

Todo modelo novo precisa ser importado aqui, para que `Base.metadata` o conheça
e o Alembic consiga gerar a migração automaticamente.
"""

from codice.db.base import Base

__all__ = ["Base"]
