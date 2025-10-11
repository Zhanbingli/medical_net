from functools import lru_cache
from typing import List
from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Drug Interaction Knowledge Graph"
    debug: bool = True
    database_url: PostgresDsn = PostgresDsn("postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet")
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    api_prefix: str = "/api/v1"
    graphql_path: str = "/graphql"

    # CORS配置 - 生产环境应设置具体域名
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # 速率限制配置
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60  # 每分钟最多请求数
    rate_limit_per_hour: int = 1000  # 每小时最多请求数

    # AI API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # AI Model Configuration
    ai_model: str = "gpt-4o-mini"  # gpt-4o-mini, gpt-4o, claude-3-5-sonnet-20241022
    ai_temperature: float = 0.3
    ai_max_tokens: int = 2000

    # External API URLs
    rxnorm_api_base: str = "https://rxnav.nlm.nih.gov/REST"
    openfda_api_base: str = "https://api.fda.gov"

    # 安全配置
    secret_key: str = "change-this-in-production"  # JWT密钥，生产环境必须修改
    access_token_expire_minutes: int = 30

    @field_validator("openai_api_key", "anthropic_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """验证API密钥不为默认值"""
        if v and v.startswith("your-") and v.endswith("-here"):
            raise ValueError(f"{info.field_name} 不能使用默认占位符值，请配置真实的API密钥")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
