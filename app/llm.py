"""Call Gemini in JSON mode; the only module that talks to the LLM provider."""

import os
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings

DEFAULT_MODEL = "gemini-3.5-flash-lite"  # 2.5-flash returned 404; 3.5-flash timed out (504)
TIMEOUT_MS = 20_000


class LLMUnavailable(Exception):
    """The LLM is not configured or the call failed."""


@lru_cache
def get_client(api_key: str) -> genai.Client:
    """One Gemini client per API key, with a 20 second timeout."""
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))


def model_name() -> str:
    """Gemini model id, overridable with GEMINI_MODEL."""
    return os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


def complete_json(system: str, user: str, schema: dict[str, Any] | None = None) -> str:
    """Send a system prompt and a user message; return the model's raw JSON text."""
    api_key = get_settings().gemini_api_key
    if not api_key:
        raise LLMUnavailable("GEMINI_API_KEY is not set.")
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_json_schema=schema,
        temperature=0.2,
    )
    try:
        response = get_client(api_key).models.generate_content(
            model=model_name(), contents=user, config=config,
        )
    except Exception as exc:  # network, quota, bad model name, timeout ...
        # Only the error type and HTTP code are kept, so no request details leak into logs.
        code = getattr(exc, "code", None)
        detail = f"{type(exc).__name__}" + (f" {code}" if code else "")
        raise LLMUnavailable(f"Gemini call failed ({detail}).") from None
    if not response.text:
        raise LLMUnavailable("Gemini returned an empty response.")
    return response.text
