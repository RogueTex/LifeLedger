from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = (
    "Answer only from provided insights JSON, cite dollar amounts and dates, "
    "2-3 sentences max"
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def generate_narrative(question: str, insights_json: Any) -> str:
    """Generate a concise narrative answer grounded only in insights JSON."""
    load_dotenv(_project_root() / ".env")

    client = OpenAI()

    insights_payload = insights_json
    if not isinstance(insights_json, str):
        insights_payload = json.dumps(insights_json, indent=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
