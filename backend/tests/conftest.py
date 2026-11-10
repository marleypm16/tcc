"""Fixtures compartilhadas.

- `tests/unit/`: sem I/O; portas substituídas por fakes em memória.
- `tests/integration/`: usam o PostgreSQL de testes do Docker Compose (marcador `integration`).
"""

import os

import pytest

DATABASE_URL_TESTES = os.environ.get(
    "DATABASE_URL_TESTES",
    "postgresql+psycopg://lastro:lastro@localhost:5432/lastro_testes",
)


@pytest.fixture(scope="session")
def database_url_testes() -> str:
    return DATABASE_URL_TESTES
