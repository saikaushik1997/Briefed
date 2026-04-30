from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://briefed:briefed@localhost:5432/briefed"
    redis_url: str = "redis://localhost:6379"

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    langsmith_api_key: str = ""
    langchain_tracing_v2: str = "true"
    langchain_project: str = "briefed"

    mlflow_tracking_uri: str = "http://localhost:5050"

    cloudflare_r2_bucket: str = ""
    cloudflare_r2_access_key: str = ""
    cloudflare_r2_secret_key: str = ""
    cloudflare_r2_endpoint: str = ""

    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
