from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ByteBeacon"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    DATABASE_URL: str
    DATABASE_SYNC_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()