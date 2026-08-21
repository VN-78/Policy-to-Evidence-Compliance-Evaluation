import json
import logging

from app.core.llm import generate_structured_json
from app.models.schema import PolicyExtractionPayload

logger = logging.getLogger(__name__)


def _clean_json_markdown(raw_content: str) -> str:
    """Strips potential Markdown wrappers (```json ... ```) returned by LLMs."""
    cleaned = raw_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


async def extract_rules_from_text(
    policy_text: str,
    provider: str | None = None,
) -> PolicyExtractionPayload:
    """
    Extracts structured compliance rules from unstructured policy text.
    Delegates LLM generation to the core LLM subsystem and deterministically validates
    the resulting JSON against PolicyExtractionPayload.
    """
    # 1. Generate schema string for prompt injection
    schema_json = json.dumps(PolicyExtractionPayload.model_json_schema(), indent=2)

    system_prompt = (
        "You are an enterprise compliance auditor. "
        "Extract machine-evaluatable rules from the provided policy document.\n"
        "You MUST respond ONLY with a JSON object conforming strictly to this JSON Schema:\n"
        f"{schema_json}\n"
        "Do not include any conversational text or explanations outside the JSON."
    )

    # 2. Call core LLM subsystem
    raw_json = await generate_structured_json(
        prompt=policy_text,
        system_instruction=system_prompt,
        provider=provider,
    )

    # 3. Clean and validate payload
    cleaned_json = _clean_json_markdown(raw_json)
    validated_payload = PolicyExtractionPayload.model_validate_json(cleaned_json)

    logger.info("Successfully extracted policy: '%s' with %d rules", validated_payload.policy_name, len(validated_payload.rules))
    return validated_payload
