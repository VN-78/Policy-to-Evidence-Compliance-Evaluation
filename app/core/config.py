from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Base Template"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
