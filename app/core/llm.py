import logging
from google import genai
from google.genai import types
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Model Fallback Chains
GEMINI_FALLBACK_MODELS: list[str] = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
]

OPENROUTER_FALLBACK_MODELS: list[str] = [
    "openrouter/free",
    "dots-studio/dots-3-note-preview:free",
    "openai/gpt-oss-20b:free",
]

OPENROUTER_PROVIDER_CONFIG: dict[str, object] = {
    "allow_fallbacks": True,
    "sort": "throughput",
    "data_collection": "allow",
}


def get_gemini_client() -> genai.Client:
    """Returns a Google GenAI Client instance configured with settings."""
    return genai.Client(api_key=settings.gemini_api_key)


def get_openrouter_client() -> AsyncOpenAI:
    """Returns an AsyncOpenAI client instance configured for OpenRouter."""
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


# Module-level instances for direct access
gemini_client = get_gemini_client()
openrouter_client = get_openrouter_client()


async def _generate_gemini(prompt: str, system_instruction: str) -> str:
    """Executes structured JSON generation using the Google Gemini API with model fallback."""
    last_error: Exception | None = None
    client = get_gemini_client()

    try:
        for model_name in GEMINI_FALLBACK_MODELS:
            try:
                logger.info("Generating via Gemini model: %s", model_name)
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if not response.text:
                    raise ValueError("Gemini returned empty text response.")
                return response.text
            except Exception as err:
                logger.warning("Gemini model %s failed: %s. Falling back to next model...", model_name, str(err))
                last_error = err
    finally:
        await client.aio.aclose()

    raise RuntimeError(f"All Gemini models failed generation. Last error: {last_error}")


async def _generate_openrouter(prompt: str, system_instruction: str) -> str:
    """Executes structured JSON generation using OpenRouter API with model fallback and provider routing."""
    last_error: Exception | None = None
    client = get_openrouter_client()

    for model_name in OPENROUTER_FALLBACK_MODELS:
        try:
            logger.info("Generating via OpenRouter model: %s", model_name)
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                extra_body={"provider": OPENROUTER_PROVIDER_CONFIG},
            )
            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("OpenRouter returned empty content payload.")
            return raw_content
        except Exception as err:
            logger.warning("OpenRouter model %s failed: %s. Falling back to next model...", model_name, str(err))
            last_error = err

    raise RuntimeError(f"All OpenRouter models failed generation. Last error: {last_error}")


async def generate_structured_json(
    prompt: str,
    system_instruction: str,
    provider: str | None = None,
) -> str:
    """
    Unified entry point for structured LLM generation.
    Routes to the configured provider (default: settings.LLM_PROVIDER).
    """
    active_provider = (provider or settings.LLM_PROVIDER).lower()

    if active_provider == "gemini":
        return await _generate_gemini(prompt, system_instruction)
    elif active_provider == "openrouter":
        return await _generate_openrouter(prompt, system_instruction)
    else:
        raise ValueError(f"Unsupported LLM provider backend: '{active_provider}'")
