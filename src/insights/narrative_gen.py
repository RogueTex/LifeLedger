from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = (
    "Answer only from provided insights JSON, cite dollar amounts and dates, "
    "2-3 sentences max. Use plain text only with normal spacing; no markdown symbols."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_client_and_model() -> tuple[OpenAI, str]:
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


def generate_narrative(question: str, insights_json: Any) -> str:
    """Generate a concise narrative answer grounded only in insights JSON."""
    load_dotenv(_project_root() / ".env")

    client, model = _build_client_and_model()

    insights_payload = insights_json
    if not isinstance(insights_json, str):
        insights_payload = json.dumps(insights_json, indent=2)

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nInsights JSON:\n{insights_payload}",
            },
        ],
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""
