from __future__ import annotations

import re
from typing import Any

import pandas as pd

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

INVOICE_KEYWORD_RE = re.compile("|".join(re.escape(k) for k in INVOICE_PAYMENT_KEYWORDS), re.IGNORECASE)
MONEY_AMOUNT_PATTERN = re.compile(r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")
LABELED_AMOUNT_PATTERN = re.compile(
    r"\b(?:amount|total|paid|payment|remit|bill(?:ed)?)\D{0,24}"
    r"(\d{2,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
HOURS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", re.IGNORECASE)

WORRY_THEME_LEXICON: dict[str, tuple[str, ...]] = {
    "anxiety": ("anxiety", "anxious", "nervous", "panic"),
    "stress": ("stress", "stressed", "pressure", "worried", "worry"),
    "burnout": ("burnout", "burned out", "exhausted"),
    "money": ("money", "budget", "cash", "rent", "afford", "bills", "paycheck"),
    "debt": ("debt", "credit card", "minimum payment"),
    "career": ("career", "promotion", "manager", "director", "client", "scope creep"),
    "relationship": ("partner", "roommate", "relationship", "family"),
}


def _row_text(row: pd.Series, columns: tuple[str, ...]) -> str:
    parts: list[str] = []
    for col in columns:
        if col not in row:
            continue
        value = row[col]
        if value is None:
            continue
        if isinstance(value, list):
            parts.extend(str(item) for item in value if item is not None)
            continue
        if pd.isna(value):
            continue
        parts.append(str(value))
    return " ".join(parts).strip()


def _source_id(row: pd.Series, idx: Any, prefix: str) -> str:
    for col in ("id", "message_id", "event_id", "source_id"):
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    return f"{prefix}_{idx}"


def _ts_value(row: pd.Series) -> str | None:
    for col in ("ts", "date", "created_at", "start"):
        if col in row and pd.notna(row[col]):
            return str(row[col])
    return None


def _extract_amounts(text: str) -> list[float]:
    values: list[float] = []
    for pattern in (MONEY_AMOUNT_PATTERN, LABELED_AMOUNT_PATTERN):
        for match in pattern.findall(text):
            try:
                value = round(float(match.replace(",", "")), 2)
            except (TypeError, ValueError):
                continue
            if value not in values:
                values.append(value)
    return values


def extract_invoice_facts(emails_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract typed invoice/payment facts from normalized email rows."""
    if emails_df is None or emails_df.empty:
        return []

    facts: list[dict[str, Any]] = []
    for idx, row in emails_df.iterrows():
        raw_text = _row_text(row, ("subject", "text", "body", "snippet", "summary", "description"))
        if not raw_text or not INVOICE_KEYWORD_RE.search(raw_text):
            continue

        amounts = _extract_amounts(raw_text)

        hours: list[float] = []
        for match in HOURS_PATTERN.findall(raw_text):
            try:
                hours.append(round(float(match), 2))
            except (TypeError, ValueError):
                continue

        if not amounts:
            continue

        confidence = 0.92 if hours else 0.76
        facts.append(
            {
                "type": "invoice_payment",
                "source": "email",
                "source_id": _source_id(row, idx, "email"),
                "ts": _ts_value(row),
                "amounts": amounts,
                "hours": hours,
                "evidence_span": raw_text[:220],
                "confidence": confidence,
                "extraction_method": "regex_invoice_v1",
            }
        )

    return facts


def extract_worry_facts(conversations_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract lightweight worry/theme facts from AI conversation exports."""
    if conversations_df is None or conversations_df.empty:
        return []

    facts: list[dict[str, Any]] = []
    for idx, row in conversations_df.iterrows():
        raw_text = _row_text(row, ("title", "text", "subject", "summary", "description", "tags"))
        if not raw_text:
            continue

        lower_text = raw_text.lower()
        themes = [
            theme
            for theme, keywords in WORRY_THEME_LEXICON.items()
            if any(keyword in lower_text for keyword in keywords)
        ]
        if not themes:
            continue

        facts.append(
            {
                "type": "worry_signal",
                "source": "ai_chat",
                "source_id": _source_id(row, idx, "conversation"),
                "ts": _ts_value(row),
                "themes": themes,
                "evidence_span": raw_text[:220],
                "confidence": 0.72,
                "extraction_method": "lexicon_worry_v1",
            }
        )

    return facts
