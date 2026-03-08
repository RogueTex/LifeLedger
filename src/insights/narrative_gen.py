from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

MAX_PAYLOAD_CHARS = 12_000
MAX_RETRIES = 3
RETRY_DELAYS = (1, 2, 4)

SYSTEM_PROMPT = (
    "You are a friendly financial advisor having a casual conversation. "
    "Answer based only on the provided insights data. Use plain everyday language "
    "— no jargon, no technical terms like 'correlation', 'statistically significant', "
    "'r-value', or 'p-value'. Talk like you're explaining things to a friend. "
    "Mention specific dollar amounts and days/weeks when relevant. Keep it to 2-3 "
    "sentences. If the data doesn't have enough info to answer, say so honestly and "
    "suggest what data they could add. No markdown or special formatting."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_client_and_model() -> tuple[OpenAI, str]:
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return (
            OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
            ),
            model,
        )

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        return (
            OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            model,
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAI(), model


def _truncate_payload(payload: str) -> str:
    """Truncate insights payload to stay within token-safe character limits."""
    if len(payload) <= MAX_PAYLOAD_CHARS:
        return payload
    truncated = payload[:MAX_PAYLOAD_CHARS]
    return truncated + "\n... [truncated — payload exceeded limit]"


def generate_narrative(question: str, insights_json: Any) -> str:
    """Generate a concise narrative answer grounded only in insights JSON."""
    load_dotenv(_project_root() / ".env")

    client, model = _build_client_and_model()

    insights_payload = insights_json
    if not isinstance(insights_json, str):
        insights_payload = json.dumps(insights_json, indent=2)

    insights_payload = _truncate_payload(insights_payload)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question: {question}\n\nInsights JSON:\n{insights_payload}",
        },
    ]

    # Retry with exponential backoff for transient API errors
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=messages,
            )
            break
        except (ConnectionError, TimeoutError) as exc:
            last_exc = exc
            logger.warning("API call failed (attempt %d/%d): %s", attempt + 1, MAX_RETRIES, exc)
        except Exception as exc:
            # Catch rate-limit and other transient OpenAI errors
            if "rate" in str(exc).lower() or "timeout" in str(exc).lower():
                last_exc = exc
                logger.warning("API call failed (attempt %d/%d): %s", attempt + 1, MAX_RETRIES, exc)
            else:
                raise
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAYS[attempt])
    else:
        return f"Unable to generate narrative (API unavailable after {MAX_RETRIES} retries)."

    # Safe response parsing
    try:
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except (AttributeError, IndexError, TypeError) as exc:
        logger.error("Malformed API response: %s", exc)
        return ""
