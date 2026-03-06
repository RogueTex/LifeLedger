from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from ..features.correlation import compute_correlation
from ..features.spend_tagger import tag_spend
from ..features.stress_scorer import compute_stress
from ..loaders.persona_loader import load_persona

ANXIETY_THEMES: tuple[str, ...] = (
    "anxiety",
    "stress",
    "burnout",
    "overwhelm",
    "career",
    "money",
    "debt",
    "relationship",
)

INVOICE_PAYMENT_KEYWORDS: tuple[str, ...] = (
    "invoice",
    "payment",
    "pay",
    "paid",
    "bill",
    "billed",
    "remit",
    "wire",
    "ach",
)

AMOUNT_PATTERN = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")
HOURS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)", re.IGNORECASE)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _profile_number(profile: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in profile and profile[key] is not None:
            try:
                return float(profile[key])
            except (TypeError, ValueError):
                pass

    financial = profile.get("financial") or profile.get("finance") or profile.get("goals") or {}
    if isinstance(financial, dict):
        for key in keys:
            if key in financial and financial[key] is not None:
                try:
                    return float(financial[key])
                except (TypeError, ValueError):
                    pass

    return None


def _compute_anxiety_themes(conversations_df: pd.DataFrame) -> list[dict[str, Any]]:
    if conversations_df is None or conversations_df.empty or "tags" not in conversations_df.columns:
        return []

    target = set(ANXIETY_THEMES)
    counts: Counter[str] = Counter()

    for tags in conversations_df["tags"]:
        tag_list = tags if isinstance(tags, list) else [tags]
        for tag in tag_list:
            normalized = str(tag).strip().lower()
            if normalized in target:
                counts[normalized] += 1

    return [{"theme": t, "count": c} for t, c in counts.most_common()]


def _extract_email_text(row: pd.Series) -> str:
    parts: list[str] = []
    for col in ("subject", "text", "body", "snippet", "summary", "description"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts).strip().lower()


def _scan_email_hourly_rate_risk(emails_df: pd.DataFrame) -> dict[str, Any]:
    if emails_df is None or emails_df.empty:
        return {"flagged": False, "matches": []}

    keyword_re = re.compile("|".join(re.escape(k) for k in INVOICE_PAYMENT_KEYWORDS), re.IGNORECASE)

    matches: list[dict[str, Any]] = []
    for _, row in emails_df.iterrows():
        text = _extract_email_text(row)
        if not text or not keyword_re.search(text):
            continue

        amounts = [float(a.replace(",", "")) for a in AMOUNT_PATTERN.findall(text)]
        hours = [float(h) for h in HOURS_PATTERN.findall(text)]
        if not amounts or not hours:
            continue

        implied_rate = min(amount / hour for amount in amounts for hour in hours if hour > 0)
        if implied_rate < 65:
            date_value = row.get("date")
            if pd.isna(date_value):
                date_value = row.get("ts")
            matches.append(
                {
                    "date": None if pd.isna(date_value) else str(date_value),
                    "implied_hourly_rate": round(float(implied_rate), 2),
                    "amounts_detected": [round(float(v), 2) for v in amounts],
                    "hours_detected": [round(float(v), 2) for v in hours],
                }
            )

    return {"flagged": bool(matches), "matches": matches}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value) if not isinstance(value, (str, bytes, dict, list, tuple)) else False:
        return None
    try:
        import numpy as np

        if isinstance(value, (np.integer, np.floating)):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    except Exception:
        pass
    return value


def compute_insights(persona_id: str) -> dict[str, Any]:
    persona_data = load_persona(persona_id)

    profile = persona_data.get("persona_profile", {})
    profile_name = profile.get("name") or profile.get("profile_name") or f"persona_{persona_id}"

    calendar_df = persona_data.get("calendar", pd.DataFrame())
    transactions_df = persona_data.get("transactions", pd.DataFrame())
    conversations_df = persona_data.get("conversations", pd.DataFrame())
    emails_df = persona_data.get("emails", pd.DataFrame())

    stress_df = compute_stress(calendar_df)
    tagged_df, weekly_spend_df = tag_spend(transactions_df)
    correlation = compute_correlation(stress_df, weekly_spend_df, tagged_df, calendar_df)

    anxiety_themes = _compute_anxiety_themes(conversations_df)

    savings_goal = _profile_number(profile, "savings_goal")
    current_savings = _profile_number(profile, "current_savings")
    avg_net_monthly_savings = _profile_number(profile, "avg_net_monthly_savings")

    months_to_goal: float | None = None
    if (
        savings_goal is not None
        and current_savings is not None
        and avg_net_monthly_savings is not None
        and avg_net_monthly_savings > 0
    ):
        months_to_goal = (savings_goal - current_savings) / avg_net_monthly_savings

    insights: list[dict[str, Any]] = [
        {"type": "stress_spend_correlation", "value": correlation},
        {"type": "top_anxiety_themes", "value": anxiety_themes},
        {
            "type": "months_to_goal",
            "value": {
                "months_to_goal": months_to_goal,
                "savings_goal": savings_goal,
                "current_savings": current_savings,
                "avg_net_monthly_savings": avg_net_monthly_savings,
            },
        },
    ]

    if persona_id == "p05":
        insights.append(
            {
                "type": "invoice_rate_risk",
                "value": _scan_email_hourly_rate_risk(emails_df),
            }
        )

    result = {
        "persona": persona_id,
        "profile_name": profile_name,
        "insights": insights,
    }
    return _jsonable(result)


def save_insights(persona_id: str) -> dict[str, Any]:
    result = compute_insights(persona_id)
    output_dir = _project_root() / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"insights_{persona_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
