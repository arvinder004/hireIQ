from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_pro_model: str = "gemini-3.6-flash"

    # Groq (Fallback)
    groq_api_key: str = ""

    # MongoDB
    mongo_uri: str
    mongo_db_name: str = "hireiq"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # SMTP (Gmail fallback)
    smtp_email: str = ""
    smtp_password: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_from_name: str = "HireIQ"

    # App
    frontend_url: str = "http://localhost:5173"
    debug: bool = True


settings = Settings()