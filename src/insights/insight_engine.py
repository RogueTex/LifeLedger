from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
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

REQUIRED_INSIGHT_FIELDS = ("id", "title", "finding", "evidence", "dollar_impact")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _profile_number(profile: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in profile and profile[key] is not None:
            try:
                return float(profile[key])
            except (TypeError, ValueError):
                pass

    for container_key in ("financial", "finance"):
        nested = profile.get(container_key)
        if isinstance(nested, dict):
            for key in keys:
                if key in nested and nested[key] is not None:
                    try:
                        return float(nested[key])
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
        return {"flagged": False, "matches": [], "estimated_monthly_leakage": None}

    keyword_re = re.compile("|".join(re.escape(k) for k in INVOICE_PAYMENT_KEYWORDS), re.IGNORECASE)

    matches: list[dict[str, Any]] = []
    leakage_samples: list[float] = []
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
            leakage_samples.append(max(0.0, 65.0 - implied_rate) * max(hours))
            matches.append(
                {
                    "date": None if pd.isna(date_value) else str(date_value),
                    "implied_hourly_rate": round(float(implied_rate), 2),
                    "amounts_detected": [round(float(v), 2) for v in amounts],
                    "hours_detected": [round(float(v), 2) for v in hours],
                }
            )

    monthly_leakage = round(sum(leakage_samples), 2) if leakage_samples else None
    return {
        "flagged": bool(matches),
        "matches": matches,
        "estimated_monthly_leakage": monthly_leakage,
    }


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


def _validate_insight_schema(result: dict[str, Any]) -> None:
    if "insights" not in result or not isinstance(result["insights"], list):
        raise ValueError("Insights contract mismatch: top-level `insights` list missing")

    seen_ids: set[str] = set()
    for idx, insight in enumerate(result["insights"]):
        if not isinstance(insight, dict):
            raise ValueError(f"Insight at index {idx} must be an object")

        for field in REQUIRED_INSIGHT_FIELDS:
            if field not in insight:
                raise ValueError(f"Insight `{insight.get('id', idx)}` missing required field `{field}`")

        insight_id = insight["id"]
        if not isinstance(insight_id, str) or not insight_id.strip():
            raise ValueError(f"Insight at index {idx} has invalid `id`")
        if insight_id in seen_ids:
            raise ValueError(f"Duplicate insight id: {insight_id}")
        seen_ids.add(insight_id)

        if not isinstance(insight["evidence"], list):
            raise ValueError(f"Insight `{insight_id}` field `evidence` must be a list")


def compute_insights(persona_id: str) -> dict[str, Any]:
    persona_data = load_persona(persona_id)

    profile = persona_data["profile"]
    consent = persona_data["consent"]
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

    correlation_value = correlation.get("correlation_coefficient")
    spikes = correlation.get("spike_weeks", [])
    avoidable_spend = 0.0
    for week in spikes:
        math_row = week.get("threshold_math", {})
        spend = float(math_row.get("week_spend", 0.0))
        mean = float(math_row.get("mean", 0.0))
        avoidable_spend += max(0.0, spend - mean)

    stress_insight = {
        "id": "stress_spend_correlation",
        "title": "Stress and discretionary spend pattern",
        "finding": correlation.get("interpretation"),
        "evidence": [
            f"Correlation coefficient: {correlation_value:.2f}" if correlation_value is not None else "Correlation coefficient unavailable",
            f"Spike weeks detected: {len(spikes)}",
            correlation.get("suggestion"),
        ],
        "dollar_impact": round(avoidable_spend, 2) if avoidable_spend > 0 else None,
        "correlation_coefficient": correlation_value,
        "p_value": correlation.get("p_value"),
        "insufficient_variance": bool(correlation.get("insufficient_variance")),
        "lag_used": correlation.get("lag_used"),
        "spike_weeks": spikes,
        "what_this_means": (
            "Your spending peaks are likely linked to stressful weeks."
            if not correlation.get("insufficient_variance")
            else "There is not enough week-to-week variation yet to estimate a stable stress/spend relationship."
        ),
        "recommended_next_actions": [
            "Review the highest-spend week and pre-plan one lower-cost alternative activity.",
            "Block one recovery hour in the prior week when calendar stress is high.",
        ],
    }

    theme_text = ", ".join(f"{item['theme']} ({item['count']})" for item in anxiety_themes[:3])
    themes_insight = {
        "id": "top_anxiety_themes",
        "title": "Recurring anxiety themes",
        "finding": (
            f"Most repeated themes: {theme_text}." if anxiety_themes else "No recurring anxiety theme was detected from current conversation tags."
        ),
        "evidence": [
            f"Theme rows analyzed: {len(anxiety_themes)}",
            "Themes are extracted from tagged conversation records only.",
        ],
        "dollar_impact": None,
        "top_themes": anxiety_themes,
        "what_this_means": "These themes explain where emotional load is most persistent.",
        "recommended_next_actions": [
            "Choose one recurring theme and schedule a concrete mitigation task this week.",
            "Use weekly check-ins to track whether theme frequency is dropping.",
        ],
    }

    months_finding = (
        f"At the current pace, goal is {months_to_goal:.1f} months away."
        if months_to_goal is not None
        else "Savings velocity cannot be computed from the current profile fields."
    )
    remaining_to_goal = None
    if savings_goal is not None and current_savings is not None:
        remaining_to_goal = round(max(0.0, savings_goal - current_savings), 2)

    goal_insight = {
        "id": "months_to_goal",
        "title": "Savings goal velocity",
        "finding": months_finding,
        "evidence": [
            f"Savings goal: {savings_goal if savings_goal is not None else 'N/A'}",
            f"Current savings: {current_savings if current_savings is not None else 'N/A'}",
            f"Avg net monthly savings: {avg_net_monthly_savings if avg_net_monthly_savings is not None else 'N/A'}",
        ],
        "dollar_impact": remaining_to_goal,
        "months_to_goal": months_to_goal,
        "savings_goal": savings_goal,
        "current_savings": current_savings,
        "avg_net_monthly_savings": avg_net_monthly_savings,
        "what_this_means": (
            "You have a measurable runway to your target savings goal."
            if months_to_goal is not None
            else "Add structured savings fields in profile data to unlock this projection."
        ),
        "recommended_next_actions": [
            "Set a weekly transfer amount and automate it on payday.",
            "Audit one discretionary category to increase monthly net savings.",
        ],
    }

    insights: list[dict[str, Any]] = [stress_insight, themes_insight, goal_insight]

    if persona_id == "p05":
        rate_payload = _scan_email_hourly_rate_risk(emails_df)
        matches = rate_payload.get("matches") or []
        rate_insight = {
            "id": "invoice_rate_risk",
            "title": "Freelance rate risk",
            "finding": (
                "Detected invoices that imply hourly rates below the $65 baseline."
                if rate_payload.get("flagged")
                else "No undercharging signal detected in the cached email data."
            ),
            "evidence": [
                f"Low-rate matches: {len(matches)}",
                f"Estimated leakage: ${rate_payload.get('estimated_monthly_leakage') if rate_payload.get('estimated_monthly_leakage') is not None else 'N/A'}",
            ],
            "dollar_impact": rate_payload.get("estimated_monthly_leakage"),
            "flagged": bool(rate_payload.get("flagged")),
            "matches": matches,
            "what_this_means": "Your pricing floor may be below sustainable market rates.",
            "recommended_next_actions": [
                "Set a minimum acceptable hourly floor before sending the next quote.",
                "Package scope in tiers so clients can trade scope instead of rate.",
            ],
        }
        insights.append(rate_insight)

    result = {
        "schema_version": "v1_locked",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "persona": persona_id,
        "profile_name": profile_name,
        "consent": {
            "dataset_type": consent.get("dataset_type"),
            "allowed_uses": consent.get("allowed_uses", []),
            "prohibited_uses": consent.get("prohibited_uses", []),
            "retention": consent.get("retention"),
            "notes": consent.get("notes"),
        },
        "insights": insights,
    }

    result = _jsonable(result)
    _validate_insight_schema(result)
    return result


def save_insights(persona_id: str) -> dict[str, Any]:
    result = compute_insights(persona_id)
    _validate_insight_schema(result)

    output_dir = _project_root() / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"insights_{persona_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
