from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8081"
    api_key: str = "change-me"
    rate_limit_per_minute: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
