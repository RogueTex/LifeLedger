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
MONEY_K_PATTERN = re.compile(r"\$?\s*(\d+(?:\.\d+)?)\s*k\b", re.IGNORECASE)
YEARLY_INCOME_PATTERN = re.compile(r"\$?\s*(\d{2,3}(?:,\d{3})?)\s*/?\s*year", re.IGNORECASE)
TIMELINE_MONTHS_PATTERN = re.compile(r"within\s+(\d+)\s*months?", re.IGNORECASE)
TIMELINE_YEARS_PATTERN = re.compile(r"within\s+(\d+)\s*years?", re.IGNORECASE)

THEME_LEXICON: dict[str, tuple[str, ...]] = {
    "anxiety": ("anxiety", "anxious", "nervous", "panic"),
    "stress": ("stress", "stressed", "pressure"),
    "burnout": ("burnout", "burned out", "exhausted"),
    "overwhelm": ("overwhelmed", "overwhelm", "too much"),
    "career": ("career", "promotion", "manager", "director", "performance"),
    "money": ("money", "budget", "cash", "income", "rent"),
    "debt": ("debt", "credit card", "minimum payment"),
    "relationship": ("partner", "roommate", "relationship", "family"),
    "self_doubt": ("imposter", "self-doubt", "not good enough", "comparison"),
    "client_stress": ("client", "scope creep", "revision", "deadline"),
    "adhd": ("adhd", "focus", "procrastination", "finish projects"),
}

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


def _extract_currency_value(text: Any) -> float | None:
    if text is None:
        return None
    raw = str(text)
    k_match = MONEY_K_PATTERN.search(raw)
    if k_match:
        try:
            return float(k_match.group(1)) * 1000.0
        except (TypeError, ValueError):
            return None
    amount_match = AMOUNT_PATTERN.search(raw)
    if not amount_match:
        return None
    try:
        return float(amount_match.group(1).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _infer_yearly_income(profile: dict[str, Any]) -> float | None:
    direct = _profile_number(profile, "annual_income", "income_yearly", "yearly_income")
    if direct is not None and direct > 0:
        return direct
    income_approx = profile.get("income_approx")
    if income_approx is None:
        return None
    match = YEARLY_INCOME_PATTERN.search(str(income_approx))
    if not match:
        return _extract_currency_value(income_approx)
    try:
        return float(match.group(1).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _infer_goal_amount_from_profile(profile: dict[str, Any]) -> float | None:
    goals = profile.get("goals") or []
    if not isinstance(goals, list):
        return None
    candidates: list[float] = []
    for goal in goals:
        text = str(goal)
        if "save" in text.lower() or "pay off" in text.lower() or "debt" in text.lower():
            value = _extract_currency_value(text)
            if value is not None:
                candidates.append(value)
    return max(candidates) if candidates else None


def _infer_goal_timeline_months(profile: dict[str, Any]) -> int | None:
    goals = profile.get("goals") or []
    if not isinstance(goals, list):
        return None
    for goal in goals:
        text = str(goal)
        month_match = TIMELINE_MONTHS_PATTERN.search(text)
        if month_match:
            return int(month_match.group(1))
        year_match = TIMELINE_YEARS_PATTERN.search(text)
        if year_match:
            return int(year_match.group(1)) * 12
    return None


def _compute_anxiety_themes(conversations_df: pd.DataFrame) -> list[dict[str, Any]]:
    if conversations_df is None or conversations_df.empty:
        return []

    counts: Counter[str] = Counter()
    target = set(ANXIETY_THEMES)

    for _, row in conversations_df.iterrows():
        tags = row.get("tags", [])
        tag_list = tags if isinstance(tags, list) else [tags]
        text = " ".join(
            str(row.get(col, "")) for col in ("text", "subject", "title", "summary", "description") if row.get(col)
        ).lower()

        for tag in tag_list:
            normalized = str(tag).strip().lower()
            if normalized in target or normalized in THEME_LEXICON:
                counts[normalized] += 1

        for theme, keywords in THEME_LEXICON.items():
            if any(keyword in text for keyword in keywords):
                counts[theme] += 1

    return [{"theme": t, "count": c} for t, c in counts.most_common()]


def _extract_email_text(row: pd.Series) -> str:
    parts: list[str] = []
    for col in ("subject", "text", "body", "snippet", "summary", "description"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts).strip().lower()


def _extract_hours_from_calendar(calendar_df: pd.DataFrame, anchor_ts: pd.Timestamp) -> float:
    if calendar_df is None or calendar_df.empty:
        return 0.0
    if not isinstance(anchor_ts, pd.Timestamp) or pd.isna(anchor_ts):
        return 0.0

    cal = calendar_df.copy()
    ts = pd.to_datetime(cal.get("ts"), errors="coerce", utc=True)
    if ts.isna().all():
        return 0.0
    window_start = anchor_ts - pd.Timedelta(days=28)
    mask = (ts >= window_start) & (ts <= anchor_ts)
    if not bool(mask.any()):
        return 0.0

    text_series = cal.loc[mask, "text"].fillna("").astype(str).str.lower() if "text" in cal.columns else pd.Series([], dtype="string")
    tag_series = cal.loc[mask, "tags"] if "tags" in cal.columns else pd.Series([], dtype="object")

    total_hours = 0.0
    for idx, text in text_series.items():
        tags = tag_series.loc[idx] if idx in tag_series.index else []
        tags_list = [str(x).lower() for x in tags] if isinstance(tags, list) else []
        if not (
            any(token in text for token in ("client", "design", "freelance", "portfolio", "presentation"))
            or any(token in tags_list for token in ("client", "design", "freelance", "business_development"))
        ):
            continue
        hrs = 0.0
        for match in re.findall(r"(\d+(?:\.\d+)?)\s*h", text):
            try:
                hrs += float(match)
            except (TypeError, ValueError):
                pass
        total_hours += hrs
    return round(total_hours, 2)


def _scan_email_hourly_rate_risk(emails_df: pd.DataFrame, calendar_df: pd.DataFrame) -> dict[str, Any]:
    if emails_df is None or emails_df.empty:
        return {"flagged": False, "matches": [], "estimated_monthly_leakage": None, "method_notes": []}

    keyword_re = re.compile("|".join(re.escape(k) for k in INVOICE_PAYMENT_KEYWORDS), re.IGNORECASE)

    matches: list[dict[str, Any]] = []
    leakage_samples: list[float] = []
    method_notes: list[str] = []
    for _, row in emails_df.iterrows():
        text = _extract_email_text(row)
        if not text or not keyword_re.search(text):
            continue

        amounts = [float(a.replace(",", "")) for a in AMOUNT_PATTERN.findall(text)]
        hours = [float(h) for h in HOURS_PATTERN.findall(text)]
        ts = pd.to_datetime(row.get("ts"), errors="coerce", utc=True)
        if not hours:
            inferred_hours = _extract_hours_from_calendar(calendar_df, ts)
            if inferred_hours > 0:
                hours = [inferred_hours]
                method_notes.append("Used trailing 28-day calendar-based project hours when invoice email had no explicit hours.")
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
                    "evidence_text": str(row.get("text", ""))[:180],
                }
            )

    monthly_leakage = round(sum(leakage_samples), 2) if leakage_samples else None
    return {
        "flagged": bool(matches),
        "matches": matches,
        "estimated_monthly_leakage": monthly_leakage,
        "method_notes": sorted(set(method_notes)),
    }


def _detect_subscriptions(transactions_df: pd.DataFrame) -> dict[str, Any]:
    """Find recurring same-amount charges that look like subscriptions."""
    if transactions_df is None or transactions_df.empty:
        return {"subscriptions": [], "monthly_total": 0.0}

    df = transactions_df.copy()
    amount = pd.to_numeric(df.get("amount", 0.0), errors="coerce").fillna(0.0).abs()
    df["_abs_amount"] = amount

    text_cols = ("text", "description", "merchant", "memo")
    texts = pd.Series([""] * len(df), index=df.index)
    for col in text_cols:
        if col in df.columns:
            texts = texts + " " + df[col].fillna("").astype(str)
    df["_text"] = texts.str.strip().str.lower()

    # Group by rounded amount and description prefix
    df["_amt_key"] = df["_abs_amount"].round(2)
    df["_desc_key"] = df["_text"].str[:30]

    subs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for (amt, desc), group in df.groupby(["_amt_key", "_desc_key"]):
        if len(group) < 2 or float(amt) < 1.0:
            continue
        key = f"{amt:.2f}|{desc}"
        if key in seen:
            continue
        seen.add(key)

        # Check if charges are roughly monthly (20-40 day gaps)
        ts = pd.to_datetime(group.get("ts", group.get("date")), errors="coerce", utc=True).dropna().sort_values()
        if len(ts) < 2:
            continue
        gaps = ts.diff().dropna().dt.days
        monthly_gaps = gaps[(gaps >= 20) & (gaps <= 45)]
        if len(monthly_gaps) < 1:
            continue

        label = group.iloc[0].get("text") or group.iloc[0].get("description") or group.iloc[0].get("merchant") or "Unknown"
        subs.append({
            "name": str(label).strip()[:60],
            "amount": round(float(amt), 2),
            "occurrences": int(len(group)),
            "avg_gap_days": round(float(gaps.mean()), 1) if len(gaps) > 0 else None,
        })

    subs.sort(key=lambda s: s["amount"], reverse=True)
    monthly_total = round(sum(s["amount"] for s in subs), 2)
    return {"subscriptions": subs, "monthly_total": monthly_total}


def _compute_day_of_week_spend(transactions_df: pd.DataFrame) -> dict[str, Any]:
    """Compute average spend by day of week."""
    if transactions_df is None or transactions_df.empty:
        return {"by_day": {}, "expensive_day": None, "expensive_day_avg": None, "cheapest_day": None}

    df = transactions_df.copy()
    ts = pd.to_datetime(df.get("ts", df.get("date")), errors="coerce", utc=True)
    amount = pd.to_numeric(df.get("amount", 0.0), errors="coerce").fillna(0.0).abs()
    df["_dow"] = ts.dt.day_name()
    df["_amount"] = amount

    df = df.dropna(subset=["_dow"])
    if df.empty:
        return {"by_day": {}, "expensive_day": None, "expensive_day_avg": None, "cheapest_day": None}

    by_day = df.groupby("_dow")["_amount"].mean().round(2).to_dict()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day_ordered = {d: by_day.get(d, 0.0) for d in day_order if d in by_day}

    expensive_day = max(by_day_ordered, key=by_day_ordered.get) if by_day_ordered else None
    cheapest_day = min(by_day_ordered, key=by_day_ordered.get) if by_day_ordered else None
    overall_avg = round(sum(by_day_ordered.values()) / len(by_day_ordered), 2) if by_day_ordered else 0.0
    expensive_avg = by_day_ordered.get(expensive_day, 0.0)
    pct_above = round(((expensive_avg - overall_avg) / overall_avg) * 100, 0) if overall_avg > 0 else 0.0

    return {
        "by_day": by_day_ordered,
        "expensive_day": expensive_day,
        "expensive_day_avg": expensive_avg,
        "cheapest_day": cheapest_day,
        "overall_daily_avg": overall_avg,
        "pct_above_average": pct_above,
    }


_INFLOW_KEYWORDS = re.compile(
    r"(income|salary|payroll|paycheck|deposit|direct dep|transfer in|refund|bonus)", re.IGNORECASE,
)


def _compute_post_payday_surge(transactions_df: pd.DataFrame) -> dict[str, Any]:
    """Detect spending concentration in the 3 days after income deposits."""
    if transactions_df is None or transactions_df.empty:
        return {"detected": False, "surge_ratio": None, "payday_count": 0}

    df = transactions_df.copy()
    ts = pd.to_datetime(df.get("ts", df.get("date")), errors="coerce", utc=True)
    amount = pd.to_numeric(df.get("amount", 0.0), errors="coerce").fillna(0.0)
    df["_ts"] = ts
    df["_amount"] = amount.abs()

    text_cols = ("text", "description", "merchant", "memo")
    texts = pd.Series([""] * len(df), index=df.index)
    for col in text_cols:
        if col in df.columns:
            texts = texts + " " + df[col].fillna("").astype(str)
    df["_text"] = texts.str.lower()

    # Identify paydays (inflow transactions)
    inflow_mask = df["_text"].str.contains(_INFLOW_KEYWORDS, na=False) | (amount > 0)
    # Also check for large positive amounts as income proxy
    large_inflow = df["_amount"] > 500
    paydays = df[inflow_mask & large_inflow].copy()
    paydays = paydays.dropna(subset=["_ts"])

    if paydays.empty:
        return {"detected": False, "surge_ratio": None, "payday_count": 0}

    # For each payday, sum spending in the next 3 days
    outflows = df[amount < 0].copy() if (amount < 0).any() else df[~(inflow_mask & large_inflow)].copy()
    outflows = outflows.dropna(subset=["_ts"])

    if outflows.empty:
        return {"detected": False, "surge_ratio": None, "payday_count": int(len(paydays))}

    post_payday_spend = 0.0
    total_spend = float(outflows["_amount"].sum())

    for _, payday_row in paydays.iterrows():
        pay_ts = payday_row["_ts"]
        window_end = pay_ts + pd.Timedelta(days=3)
        in_window = outflows[(outflows["_ts"] > pay_ts) & (outflows["_ts"] <= window_end)]
        post_payday_spend += float(in_window["_amount"].sum())

    surge_ratio = round(post_payday_spend / total_spend, 2) if total_spend > 0 else 0.0
    # A surge_ratio > 0.30 means 30%+ of all spending happens in 3-day post-payday windows
    detected = surge_ratio > 0.25

    return {
        "detected": detected,
        "surge_ratio": surge_ratio,
        "surge_pct": round(surge_ratio * 100, 1),
        "post_payday_total": round(post_payday_spend, 2),
        "total_spend": round(total_spend, 2),
        "payday_count": int(len(paydays)),
    }


def _compute_worry_timeline(conversations_df: pd.DataFrame, weekly_spend_df: pd.DataFrame) -> dict[str, Any]:
    """Build a weekly timeline of worry mentions from AI conversations overlaid with spending."""
    if conversations_df is None or conversations_df.empty:
        return {"timeline": [], "peak_worry_week": None, "total_worry_mentions": 0}

    df = conversations_df.copy()
    ts = pd.to_datetime(df.get("ts", df.get("date")), errors="coerce", utc=True)
    df["_ts"] = ts
    df = df.dropna(subset=["_ts"])

    if df.empty:
        return {"timeline": [], "peak_worry_week": None, "total_worry_mentions": 0}

    iso = df["_ts"].dt.isocalendar()
    df["_year_week"] = iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)

    worry_keywords = re.compile(
        r"(anxiety|anxious|stress|worried|overwhelm|burnout|panic|nervous|scared|"
        r"money|debt|rent|budget|broke|afford|expensive|bills|paycheck)",
        re.IGNORECASE,
    )

    text_series = pd.Series([""] * len(df), index=df.index)
    for col in ("text", "subject", "title", "summary", "description"):
        if col in df.columns:
            text_series = text_series + " " + df[col].fillna("").astype(str)

    df["_worry"] = text_series.str.contains(worry_keywords, na=False).astype(int)

    weekly_worry = df.groupby("_year_week")["_worry"].sum().reset_index()
    weekly_worry.columns = ["year_week", "worry_mentions"]

    # Merge with spending if available
    if weekly_spend_df is not None and not weekly_spend_df.empty:
        spend_lookup = dict(zip(weekly_spend_df["year_week"], weekly_spend_df["weekly_discretionary_total"]))
    else:
        spend_lookup = {}

    timeline = []
    for _, row in weekly_worry.iterrows():
        yw = str(row["year_week"])
        timeline.append({
            "year_week": yw,
            "worry_mentions": int(row["worry_mentions"]),
            "discretionary_spend": spend_lookup.get(yw, 0.0),
        })

    timeline.sort(key=lambda r: r["year_week"])
    total = sum(r["worry_mentions"] for r in timeline)
    peak = max(timeline, key=lambda r: r["worry_mentions"]) if timeline else None

    return {
        "timeline": timeline,
        "peak_worry_week": peak["year_week"] if peak and peak["worry_mentions"] > 0 else None,
        "peak_worry_spend": peak.get("discretionary_spend") if peak else None,
        "total_worry_mentions": total,
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
    estimation_mode = "direct_profile_fields"
    inference_notes: list[str] = []

    if savings_goal is None:
        inferred_goal = _infer_goal_amount_from_profile(profile)
        if inferred_goal is not None:
            savings_goal = inferred_goal
            estimation_mode = "inferred_goal_amount"
            inference_notes.append("Inferred goal amount from profile goal text.")

    if avg_net_monthly_savings is None:
        yearly_income = _infer_yearly_income(profile)
        if yearly_income is not None and yearly_income > 0:
            avg_net_monthly_savings = round((yearly_income / 12.0) * 0.10, 2)
            estimation_mode = "income_proxy_10pct"
            inference_notes.append("Estimated monthly savings as 10% of stated annual income.")
    if current_savings is None and savings_goal is not None:
        current_savings = 0.0
        if estimation_mode != "direct_profile_fields":
            inference_notes.append("Assumed current savings baseline as 0 due to missing profile field.")

    months_to_goal: float | None = None
    if (
        savings_goal is not None
        and current_savings is not None
        and avg_net_monthly_savings is not None
        and avg_net_monthly_savings > 0
    ):
        months_to_goal = (savings_goal - current_savings) / avg_net_monthly_savings
    if months_to_goal is None:
        timeline_months = _infer_goal_timeline_months(profile)
        if timeline_months is not None and timeline_months > 0:
            months_to_goal = float(timeline_months)
            estimation_mode = "profile_goal_timeline"
            inference_notes.append("Used explicit timeline found in profile goals.")

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
        "weekly_series": correlation.get("weekly_series", []),
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
            f"Most repeated themes: {theme_text}."
            if anxiety_themes
            else "No recurring anxiety theme was detected from current conversation text and tags."
        ),
        "evidence": [
            f"Theme rows analyzed: {len(anxiety_themes)}",
            "Themes are extracted from conversation tags plus lexicon matches in message text.",
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
            f"Estimation mode: {estimation_mode}",
            *inference_notes,
        ],
        "dollar_impact": remaining_to_goal,
        "months_to_goal": months_to_goal,
        "savings_goal": savings_goal,
        "current_savings": current_savings,
        "avg_net_monthly_savings": avg_net_monthly_savings,
        "estimation_mode": estimation_mode,
        "what_this_means": (
            "You have a measurable runway to your target savings goal."
            if months_to_goal is not None
            else "Add structured savings fields in profile data to unlock a more precise projection."
        ),
        "recommended_next_actions": [
            "Set a weekly transfer amount and automate it on payday.",
            "Audit one discretionary category to increase monthly net savings.",
        ],
    }

    # --- Subscription creep ---
    sub_data = _detect_subscriptions(transactions_df)
    sub_list = sub_data["subscriptions"]
    sub_names = ", ".join(s["name"][:30] for s in sub_list[:5])
    subscription_insight = {
        "id": "subscription_creep",
        "title": "Subscription creep",
        "finding": (
            f"You have {len(sub_list)} recurring charges totaling ${sub_data['monthly_total']}/mo: {sub_names}."
            if sub_list
            else "No recurring subscription charges detected."
        ),
        "evidence": [
            f"Subscriptions detected: {len(sub_list)}",
            f"Monthly total: ${sub_data['monthly_total']}",
            f"Yearly cost: ${round(sub_data['monthly_total'] * 12, 2)}",
        ],
        "dollar_impact": round(sub_data["monthly_total"] * 12, 2) if sub_data["monthly_total"] > 0 else None,
        "subscriptions": sub_list,
        "monthly_total": sub_data["monthly_total"],
        "what_this_means": (
            "These charges repeat every month whether you use the service or not. "
            "Review each one and cancel anything you haven't used in the last 30 days."
            if sub_list
            else "No recurring patterns found in your transaction history."
        ),
        "recommended_next_actions": [
            "Open each subscription and check your last login date.",
            "Cancel one subscription you haven't used in 30 days.",
        ],
    }

    # --- Expensive day of week ---
    dow_data = _compute_day_of_week_spend(transactions_df)
    expensive_day = dow_data.get("expensive_day")
    dow_insight = {
        "id": "expensive_day_of_week",
        "title": "Your expensive day of the week",
        "finding": (
            f"You spend the most on {expensive_day}s — ${dow_data.get('expensive_day_avg', 0):.2f} avg vs ${dow_data.get('overall_daily_avg', 0):.2f} overall ({dow_data.get('pct_above_average', 0):.0f}% above average)."
            if expensive_day
            else "Not enough transaction data to determine day-of-week patterns."
        ),
        "evidence": [
            f"Average by day: {', '.join(f'{d}: ${v:.2f}' for d, v in dow_data.get('by_day', {}).items())}",
            f"Cheapest day: {dow_data.get('cheapest_day', 'N/A')}",
        ],
        "dollar_impact": None,
        "by_day": dow_data.get("by_day", {}),
        "expensive_day": expensive_day,
        "cheapest_day": dow_data.get("cheapest_day"),
        "pct_above_average": dow_data.get("pct_above_average"),
        "what_this_means": (
            f"{expensive_day} is when you're most likely to overspend. Knowing this lets you plan ahead."
            if expensive_day
            else "Add more transaction history to unlock this pattern."
        ),
        "recommended_next_actions": [
            f"Set a {expensive_day} spending cap and check it before buying." if expensive_day else "Upload more transaction data.",
            f"Pre-plan {expensive_day} meals or activities to avoid impulse purchases." if expensive_day else "Keep tracking.",
        ],
    }

    # --- Post-payday surge ---
    surge_data = _compute_post_payday_surge(transactions_df)
    surge_insight = {
        "id": "post_payday_surge",
        "title": "Post-payday spending surge",
        "finding": (
            f"{surge_data.get('surge_pct', 0)}% of your spending happens within 3 days of getting paid (${surge_data.get('post_payday_total', 0):.2f} of ${surge_data.get('total_spend', 0):.2f})."
            if surge_data.get("detected")
            else (
                f"No significant post-payday surge — {surge_data.get('surge_pct', 0)}% of spending is in the 3-day post-payday window."
                if surge_data.get("surge_ratio") is not None
                else "Could not detect income deposits to analyze payday patterns."
            )
        ),
        "evidence": [
            f"Paydays detected: {surge_data.get('payday_count', 0)}",
            f"Post-payday spend: ${surge_data.get('post_payday_total', 0)}",
            f"Total spend: ${surge_data.get('total_spend', 0)}",
            f"Surge ratio: {surge_data.get('surge_pct', 0)}%",
        ],
        "dollar_impact": surge_data.get("post_payday_total") if surge_data.get("detected") else None,
        "detected": surge_data.get("detected", False),
        "surge_pct": surge_data.get("surge_pct"),
        "what_this_means": (
            "You spend heavily right after payday, which can leave you tight before the next one. "
            "This is a common pattern — awareness is the first step."
            if surge_data.get("detected")
            else "Your spending is relatively evenly distributed across the pay cycle."
        ),
        "recommended_next_actions": [
            "Wait 24 hours after payday before any non-essential purchase.",
            "Auto-transfer savings on payday before you can spend it.",
        ],
    }

    # --- Worry timeline (cross-source) ---
    worry_data = _compute_worry_timeline(conversations_df, weekly_spend_df)
    worry_timeline = worry_data.get("timeline", [])
    peak_week = worry_data.get("peak_worry_week")
    peak_spend = worry_data.get("peak_worry_spend", 0.0)
    worry_insight = {
        "id": "worry_timeline",
        "title": "When you worry most (AI conversations x spending)",
        "finding": (
            f"You mentioned financial/emotional worries {worry_data['total_worry_mentions']} times in AI conversations. "
            f"Peak worry: week {peak_week}"
            + (f" (${peak_spend:.2f} spent that week)." if peak_spend else ".")
            if peak_week
            else "No worry-related conversations detected in your AI chat exports."
        ),
        "evidence": [
            f"Total worry mentions: {worry_data.get('total_worry_mentions', 0)}",
            f"Weeks with worry signals: {sum(1 for w in worry_timeline if w['worry_mentions'] > 0)}",
            "Sources: ChatGPT/Claude conversation exports cross-referenced with spending data.",
        ],
        "dollar_impact": None,
        "timeline": worry_timeline,
        "peak_worry_week": peak_week,
        "total_worry_mentions": worry_data.get("total_worry_mentions", 0),
        "what_this_means": (
            "Your AI conversations reveal when stress peaks. Overlaying this with spending shows "
            "whether worry translates into spending changes — something no single data source can show alone."
            if worry_data.get("total_worry_mentions", 0) > 0
            else "Upload ChatGPT or Claude exports to unlock this cross-source insight."
        ),
        "recommended_next_actions": [
            "During high-worry weeks, set a 24-hour rule on discretionary purchases.",
            "Use your AI assistant to journal about financial stress instead of spending through it.",
        ],
    }

    insights: list[dict[str, Any]] = [
        stress_insight,
        themes_insight,
        goal_insight,
        subscription_insight,
        dow_insight,
        surge_insight,
        worry_insight,
    ]

    if persona_id == "p05":
        rate_payload = _scan_email_hourly_rate_risk(emails_df, calendar_df)
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
                *rate_payload.get("method_notes", []),
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
        "metric_layer_version": None,
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


def compute_insights_from_dataframes(
    transactions_df: pd.DataFrame | None = None,
    calendar_df: pd.DataFrame | None = None,
    conversations_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Compute insights from user-uploaded DataFrames (no persona file needed)."""
    if transactions_df is None:
        transactions_df = pd.DataFrame()
    if calendar_df is None:
        calendar_df = pd.DataFrame()
    if conversations_df is None:
        conversations_df = pd.DataFrame()

    stress_df = compute_stress(calendar_df)
    tagged_df, weekly_spend_df = tag_spend(transactions_df)
    correlation = compute_correlation(stress_df, weekly_spend_df, tagged_df, calendar_df)

    anxiety_themes = _compute_anxiety_themes(conversations_df)

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
        "weekly_series": correlation.get("weekly_series", []),
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
            f"Most repeated themes: {theme_text}."
            if anxiety_themes
            else "No recurring anxiety theme was detected from current conversation text and tags."
        ),
        "evidence": [
            f"Theme rows analyzed: {len(anxiety_themes)}",
            "Themes are extracted from conversation tags plus lexicon matches in message text.",
        ],
        "dollar_impact": None,
        "top_themes": anxiety_themes,
        "what_this_means": "These themes explain where emotional load is most persistent.",
        "recommended_next_actions": [
            "Choose one recurring theme and schedule a concrete mitigation task this week.",
            "Use weekly check-ins to track whether theme frequency is dropping.",
        ],
    }

    sub_data = _detect_subscriptions(transactions_df)
    sub_list = sub_data["subscriptions"]
    sub_names = ", ".join(s["name"][:30] for s in sub_list[:5])
    subscription_insight = {
        "id": "subscription_creep",
        "title": "Subscription creep",
        "finding": (
            f"You have {len(sub_list)} recurring charges totaling ${sub_data['monthly_total']}/mo: {sub_names}."
            if sub_list
            else "No recurring subscription charges detected."
        ),
        "evidence": [
            f"Subscriptions detected: {len(sub_list)}",
            f"Monthly total: ${sub_data['monthly_total']}",
            f"Yearly cost: ${round(sub_data['monthly_total'] * 12, 2)}",
        ],
        "dollar_impact": round(sub_data["monthly_total"] * 12, 2) if sub_data["monthly_total"] > 0 else None,
        "subscriptions": sub_list,
        "monthly_total": sub_data["monthly_total"],
        "what_this_means": (
            "These charges repeat every month whether you use the service or not. "
            "Review each one and cancel anything you haven't used in the last 30 days."
            if sub_list
            else "No recurring patterns found in your transaction history."
        ),
        "recommended_next_actions": [
            "Open each subscription and check your last login date.",
            "Cancel one subscription you haven't used in 30 days.",
        ],
    }

    dow_data = _compute_day_of_week_spend(transactions_df)
    expensive_day = dow_data.get("expensive_day")
    dow_insight = {
        "id": "expensive_day_of_week",
        "title": "Your expensive day of the week",
        "finding": (
            f"You spend the most on {expensive_day}s — ${dow_data.get('expensive_day_avg', 0):.2f} avg vs ${dow_data.get('overall_daily_avg', 0):.2f} overall ({dow_data.get('pct_above_average', 0):.0f}% above average)."
            if expensive_day
            else "Not enough transaction data to determine day-of-week patterns."
        ),
        "evidence": [
            f"Average by day: {', '.join(f'{d}: ${v:.2f}' for d, v in dow_data.get('by_day', {}).items())}",
            f"Cheapest day: {dow_data.get('cheapest_day', 'N/A')}",
        ],
        "dollar_impact": None,
        "by_day": dow_data.get("by_day", {}),
        "expensive_day": expensive_day,
        "cheapest_day": dow_data.get("cheapest_day"),
        "pct_above_average": dow_data.get("pct_above_average"),
        "what_this_means": (
            f"{expensive_day} is when you're most likely to overspend. Knowing this lets you plan ahead."
            if expensive_day
            else "Add more transaction history to unlock this pattern."
        ),
        "recommended_next_actions": [
            f"Set a {expensive_day} spending cap and check it before buying." if expensive_day else "Upload more transaction data.",
            f"Pre-plan {expensive_day} meals or activities to avoid impulse purchases." if expensive_day else "Keep tracking.",
        ],
    }

    surge_data = _compute_post_payday_surge(transactions_df)
    surge_insight = {
        "id": "post_payday_surge",
        "title": "Post-payday spending surge",
        "finding": (
            f"{surge_data.get('surge_pct', 0)}% of your spending happens within 3 days of getting paid (${surge_data.get('post_payday_total', 0):.2f} of ${surge_data.get('total_spend', 0):.2f})."
            if surge_data.get("detected")
            else (
                f"No significant post-payday surge — {surge_data.get('surge_pct', 0)}% of spending is in the 3-day post-payday window."
                if surge_data.get("surge_ratio") is not None
                else "Could not detect income deposits to analyze payday patterns."
            )
        ),
        "evidence": [
            f"Paydays detected: {surge_data.get('payday_count', 0)}",
            f"Post-payday spend: ${surge_data.get('post_payday_total', 0)}",
            f"Total spend: ${surge_data.get('total_spend', 0)}",
            f"Surge ratio: {surge_data.get('surge_pct', 0)}%",
        ],
        "dollar_impact": surge_data.get("post_payday_total") if surge_data.get("detected") else None,
        "detected": surge_data.get("detected", False),
        "surge_pct": surge_data.get("surge_pct"),
        "what_this_means": (
            "You spend heavily right after payday, which can leave you tight before the next one. "
            "This is a common pattern — awareness is the first step."
            if surge_data.get("detected")
            else "Your spending is relatively evenly distributed across the pay cycle."
        ),
        "recommended_next_actions": [
            "Wait 24 hours after payday before any non-essential purchase.",
            "Auto-transfer savings on payday before you can spend it.",
        ],
    }

    worry_data = _compute_worry_timeline(conversations_df, weekly_spend_df)
    worry_timeline = worry_data.get("timeline", [])
    peak_week = worry_data.get("peak_worry_week")
    peak_spend = worry_data.get("peak_worry_spend", 0.0)
    worry_insight = {
        "id": "worry_timeline",
        "title": "When you worry most (AI conversations x spending)",
        "finding": (
            f"You mentioned financial/emotional worries {worry_data['total_worry_mentions']} times in AI conversations. "
            f"Peak worry: week {peak_week}"
            + (f" (${peak_spend:.2f} spent that week)." if peak_spend else ".")
            if peak_week
            else "No worry-related conversations detected in your AI chat exports."
        ),
        "evidence": [
            f"Total worry mentions: {worry_data.get('total_worry_mentions', 0)}",
            f"Weeks with worry signals: {sum(1 for w in worry_timeline if w['worry_mentions'] > 0)}",
            "Sources: ChatGPT/Claude conversation exports cross-referenced with spending data.",
        ],
        "dollar_impact": None,
        "timeline": worry_timeline,
        "peak_worry_week": peak_week,
        "total_worry_mentions": worry_data.get("total_worry_mentions", 0),
        "what_this_means": (
            "Your AI conversations reveal when stress peaks. Overlaying this with spending shows "
            "whether worry translates into spending changes — something no single data source can show alone."
            if worry_data.get("total_worry_mentions", 0) > 0
            else "Upload ChatGPT or Claude exports to unlock this cross-source insight."
        ),
        "recommended_next_actions": [
            "During high-worry weeks, set a 24-hour rule on discretionary purchases.",
            "Use your AI assistant to journal about financial stress instead of spending through it.",
        ],
    }

    insights: list[dict[str, Any]] = [
        stress_insight,
        themes_insight,
        subscription_insight,
        dow_insight,
        surge_insight,
        worry_insight,
    ]

    result = {
        "schema_version": "v1_locked",
        "metric_layer_version": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "persona": "upload",
        "profile_name": "Your Data",
        "consent": {
            "dataset_type": "user_upload",
            "allowed_uses": ["personal_analysis"],
            "prohibited_uses": [],
            "retention": "session_only",
            "notes": "User-uploaded data processed locally.",
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
