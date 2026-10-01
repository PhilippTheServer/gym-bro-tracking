"""Typed application settings, read once from the environment."""

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, sourced from environment variables or a local .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://gymbro:gymbro_secret@localhost:5432/gymbro"
    # Where the API reaches Keycloak (may be an internal address).
    keycloak_url: str = "http://localhost:8080"
    # The URL browsers use; tokens carry it as their issuer. Falls back to keycloak_url.
    keycloak_public_url: str = ""
    keycloak_realm: str = "gym-bro"
    keycloak_client_id: str = "gym-bro-app"
    # The Keycloak client id daily's service account authenticates as. Empty disables
    # the export route entirely.
    export_client_id: str = ""
    cors_origins: list[str] = ["http://localhost", "http://localhost:4200"]
    run_seed: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: str | list[str]) -> list[str]:
        """
        Arg: value - either a JSON array string from the environment or an actual list.
        Operation: decodes the JSON form so CORS_ORIGINS can be supplied as a string.
        Return: list of allowed origins.
        """
        if isinstance(value, str):
            return json.loads(value)
        return value

    @property
    def keycloak_jwks_uri(self) -> str:
        """
        Arg: none.
        Operation: builds the realm's JWKS endpoint from the internal Keycloak URL.
        Return: absolute JWKS URL.
        """
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_issuer(self) -> str:
        """
        Arg: none.
        Operation: builds the issuer string tokens are expected to carry, preferring the
                   public URL because that is what the browser authenticated against.
        Return: expected 'iss' claim value.
        """
        base = self.keycloak_public_url or self.keycloak_url
        return f"{base}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    """
    Arg: none.
    Operation: builds the Settings object once and caches it for the process lifetime.
    Return: the shared Settings instance.
    """
    return Settings()
