"""Engine e fábrica de sessões do SQLAlchemy."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def criar_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def criar_fabrica_sessoes(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
