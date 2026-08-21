from openai import AsyncOpenAI

from app.core.config import settings

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)
