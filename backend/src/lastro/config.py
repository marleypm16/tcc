"""Configuração lida de variáveis de ambiente (e do arquivo `.env` na raiz do repositório)."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[3]


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=RAIZ_REPOSITORIO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://lastro:lastro@localhost:5432/lastro"

    github_app_id: str = ""
    github_private_key_path: Path | None = None
    github_webhook_secret: SecretStr = SecretStr("")
    github_client_id: str = ""
    github_client_secret: SecretStr = SecretStr("")

    gemini_api_key: SecretStr = SecretStr("")
    gemini_modelo: str = "gemini-3.6-flash"

    worker_intervalo_consulta_s: float = 5.0


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
