from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import ClassVar

# Resolve path to root .env file regardless of current working directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    openrouter_api_key: str = Field(
            default="",
            description="OpenRouter API Key for LLM extraction",
    )
    
    PROJECT_NAME: str = "Policy-to-Evidence-Compliance-Evaluation"

    # This tells Pydantic to read from a local .env file
    # Pydantic Settings configuration
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=(str(ENV_PATH), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

# Instantiate it once to be imported anywhere in the app
settings = Settings()