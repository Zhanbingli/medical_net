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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
