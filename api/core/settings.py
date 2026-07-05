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


settings = Settings()
