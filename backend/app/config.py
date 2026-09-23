from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    gemini_pro_model: str = "gemini-1.5-pro"

    mongo_uri: str
    mongo_db_name: str = "hireiq"

    redis_url: str = "redis://localhost:6379"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    frontend_url: str = "http://localhost:5173"
    debug: bool = False

settings = Settings()