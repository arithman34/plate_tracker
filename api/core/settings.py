from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str
    api_prefix: str = "/api/v1"
    postgres_user: str
    postgres_password: str
    postgres_db: str
    s3_bucket: str | None = None
    aws_region: str = "eu-west-2"

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg(cls, v: str) -> str:
        # Railway's Postgres plugin (and most managed providers) hand out
        # postgres:// or postgresql:// — SQLAlchemy's async engine needs the
        # asyncpg driver spelled out explicitly.
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
