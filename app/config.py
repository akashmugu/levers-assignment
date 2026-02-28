from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Overridden by DATABASE_URL env var or .env file; this default is for local dev only.
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/billing"

    model_config = {"env_file": ".env"}


settings = Settings()
