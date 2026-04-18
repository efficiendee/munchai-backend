from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8081"
    rate_limit_per_minute: int = 120
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "munchai"
    token_ttl_hours: int = 24
    text_model_api_key: str = ""
    image_model_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
