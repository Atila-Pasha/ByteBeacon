from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ByteBeacon"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str
    DATABASE_SYNC_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CHECK_TIMEOUT: float = 10.0
    SCHEDULER_ENABLED: bool = True

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_LINK_EXPIRE_MINUTES: int = 10
    TELEGRAM_API_TIMEOUT: float = 10.0
    TELEGRAM_API_BASE_URL: str = "http://localhost:8000"
    # Set this when Telegram is only reachable through a proxy, e.g.
    # socks5://127.0.0.1:10808.
    TELEGRAM_PROXY_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
