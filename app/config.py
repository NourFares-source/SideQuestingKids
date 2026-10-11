from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SideQuest AI for Kids"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secretpassword@localhost:5432/sidequest_db"
    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()