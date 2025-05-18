from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from urllib.parse import urlparse


class Settings(BaseSettings):
    PROJECT_NAME: str = "Task Execution API"
    API_PREFIX: str = "/api"

    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"
    REDIS_URL: str = "redis://redis:6379/0"

    RABBITMQ_HOST: str = Field("rabbitmq", env="RABBITMQ_HOST")
    RABBITMQ_PORT: int = Field(5672, env="RABBITMQ_PORT")

    TASK_STATUS_UPDATE_INTERVAL: int = 5

    @validator("REDIS_URL", pre=True)
    def parse_redis_url(cls, v):
        if isinstance(v, str):
            parsed = urlparse(v)
            if parsed.scheme == "redis":
                return v
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
