from functools import lru_cache
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Drug Interaction Knowledge Graph"
    debug: bool = True
    database_url: PostgresDsn = PostgresDsn("postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet")
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    api_prefix: str = "/api/v1"
    graphql_path: str = "/graphql"

    # AI API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # AI Model Configuration
    ai_model: str = "gpt-4o-mini"  # gpt-4o-mini, gpt-4o, claude-3-5-sonnet-20241022
    ai_temperature: float = 0.3

    # External API URLs
    rxnorm_api_base: str = "https://rxnav.nlm.nih.gov/REST"
    openfda_api_base: str = "https://api.fda.gov"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
