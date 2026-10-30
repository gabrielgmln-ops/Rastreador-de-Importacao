# rastreador-importacao/backend/app/config.py
# Configuração centralizada: tudo vem de variáveis de ambiente, nada fixo no código.
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str
    secret_key: str
    # Login simples: um único usuário definido por ambiente
    admin_user: str = "admin"
    admin_password: str
    token_ttl_min: int = 480
    cors_origins: str = "http://localhost:5173"
    landed_url: str = "http://localhost:8001"
    landed_timeout_s: float = 5.0

    @property
    def cors_list(self) -> list[str]:
        """Aceita várias origens separadas por vírgula."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    # Cache: lê o ambiente uma única vez por processo
    return Settings()
