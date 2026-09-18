"""
Thin wrapper around the Groq API. Every LLM call in the app goes through
this module, so swapping providers (e.g. to Gemini) later means editing one
file, not every agent node.
"""
from __future__ import annotations

import json
from typing import Optional, Type, TypeVar

from groq import Groq
from pydantic import BaseModel, ValidationError

from config import settings

T = TypeVar("T", bound=BaseModel)

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file (see .env.example)."
            )
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def generate_text(system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
    """Plain text completion — used for explanations and narrative insights."""
    client = get_client()
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def generate_structured(system_prompt: str, user_prompt: str, schema: Type[T],
                        temperature: Optional[float] = None, max_retries: int = 2) -> T:
    """
    Forces the model to return JSON matching `schema` (a Pydantic model).
    Retries once with the validation error fed back to the model if the
    first response doesn't parse — this is what keeps the app's structured
    outputs reliable instead of "usually working".
    """
    client = get_client()
    schema_hint = json.dumps(schema.model_json_schema(), indent=2)
    full_system = (
        f"{system_prompt}\n\n"
        "Respond with ONLY a valid JSON object matching this schema. "
        "No markdown fences, no commentary before or after the JSON.\n\n"
        f"Schema:\n{schema_hint}"
    )

    messages = [
        {"role": "system", "content": full_system},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None
    for attempt in range(max_retries + 1):
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        try:
            return schema.model_validate_json(raw)
        except ValidationError as e:
            last_error = e
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"That JSON did not match the schema. Validation error:\n{e}\nReturn corrected JSON only.",
            })
            continue

    raise ValueError(f"Model failed to produce valid structured output after {max_retries + 1} attempts: {last_error}")
