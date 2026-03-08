"""Parsers for user-uploaded data files (CSV transactions, ICS calendar, ChatGPT export)."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Bank transaction CSV parser
# ---------------------------------------------------------------------------

_DATE_CANDIDATES = (
    "date", "transaction date", "trans date", "posting date", "post date",
    "transaction_date", "posted_date", "trans_date",
)
_AMOUNT_CANDIDATES = (
    "amount", "debit", "transaction amount", "trans amount",
    "amount (usd)", "transaction_amount",
)
_TEXT_CANDIDATES = (
    "description", "merchant", "name", "memo", "details",
    "transaction description", "payee", "original description",
)
_CATEGORY_CANDIDATES = (
    "category", "type", "transaction type", "trans type",
)


def _find_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower_map = {c.lower().strip(): c for c in columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def parse_transactions_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parse a bank CSV into a normalised transactions DataFrame."""
    text = file_bytes.decode("utf-8-sig", errors="replace")

    # Skip preamble lines that some banks add before the header
    lines = text.splitlines()
    header_idx = 0
    for i, line in enumerate(lines[:10]):
        if "," in line:
            sniffer_cols = [c.strip().strip('"').lower() for c in line.split(",")]
            if any(c in _flatten_candidates() for c in sniffer_cols):
                header_idx = i
                break

    reader = csv.DictReader(lines[header_idx:])
    if reader.fieldnames is None:
        return _empty_txn_df()

    cols = list(reader.fieldnames)
    date_col = _find_column(cols, _DATE_CANDIDATES)
    amount_col = _find_column(cols, _AMOUNT_CANDIDATES)
    text_col = _find_column(cols, _TEXT_CANDIDATES)
    category_col = _find_column(cols, _CATEGORY_CANDIDATES)

    if date_col is None or amount_col is None:
        return _empty_txn_df()

    rows: list[dict[str, Any]] = []
    for row in reader:
        raw_amount = _parse_amount(row.get(amount_col, ""))
        if raw_amount is None:
            continue
        ts = _parse_date(row.get(date_col, ""))
        if ts is None:
            continue
        description = row.get(text_col, "") if text_col else ""
        category = row.get(category_col, "") if category_col else ""
        rows.append({
            "id": f"t_{len(rows):04d}",
            "ts": ts,
            "source": "bank",
            "type": "transaction",
            "text": str(description).strip(),
            "tags": [category.strip().lower()] if category.strip() else [],
            "refs": [],
            "amount": abs(raw_amount),
            "pii_level": "user_upload",
        })

    if not rows:
        return _empty_txn_df()

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["date"] = df["ts"].dt.date
    iso = df["ts"].dt.isocalendar()
    df["year_week"] = (
        iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    )
    return df


def _flatten_candidates() -> set[str]:
    return set(_DATE_CANDIDATES + _AMOUNT_CANDIDATES + _TEXT_CANDIDATES + _CATEGORY_CANDIDATES)


def _parse_amount(raw: str) -> float | None:
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().replace("$", "").replace(",", "").strip("\"'() ")
    # Handle parenthetical negatives: (123.45)
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned.strip("()")
    try:
        value = float(cleaned)
        return -value if negative else value
    except ValueError:
        return None


def _parse_date(raw: str) -> datetime | None:
    if not raw or not raw.strip():
        return None
    raw = raw.strip().strip('"')
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # Fallback: let pandas try
    try:
        parsed = pd.to_datetime(raw, utc=True)
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    except Exception:
        pass
    return None


def _empty_txn_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "ts", "source", "type", "text", "tags", "refs", "amount",
        "pii_level", "date", "year_week",
    ])


# ---------------------------------------------------------------------------
# ICS calendar parser
# ---------------------------------------------------------------------------

def parse_calendar_ics(file_bytes: bytes) -> pd.DataFrame:
    """Parse an ICS file into a normalised calendar DataFrame."""
    text = file_bytes.decode("utf-8", errors="replace")
    events = _extract_vevents(text)

    if not events:
        return _empty_cal_df()

    rows: list[dict[str, Any]] = []
    for i, event in enumerate(events):
        ts = _parse_ics_datetime(event.get("DTSTART", ""))
        if ts is None:
            continue
        summary = event.get("SUMMARY", "")
        description = event.get("DESCRIPTION", "")
        combined_text = f"{summary} {description}".strip()
        rows.append({
            "id": f"cal_{i:04d}",
            "ts": ts,
            "source": "calendar",
            "type": "event",
            "text": combined_text,
            "tags": [],
            "refs": [],
            "amount": None,
            "pii_level": "user_upload",
        })

    if not rows:
        return _empty_cal_df()

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["date"] = df["ts"].dt.date
    iso = df["ts"].dt.isocalendar()
    df["year_week"] = (
        iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    )
    return df


def _extract_vevents(ics_text: str) -> list[dict[str, str]]:
    """Extract VEVENT blocks from ICS text, handling unfolded lines."""
    # Unfold continuation lines (RFC 5545: lines starting with space/tab)
    unfolded = re.sub(r"\r?\n[ \t]", "", ics_text)
    events: list[dict[str, str]] = []
    in_event = False
    current: dict[str, str] = {}
    for line in unfolded.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_event = True
            current = {}
        elif line == "END:VEVENT":
            if in_event:
                events.append(current)
            in_event = False
        elif in_event and ":" in line:
            # Handle properties with parameters like DTSTART;VALUE=DATE:20240101
            key_part, _, value = line.partition(":")
            key = key_part.split(";")[0].upper()
            current[key] = value
    return events


def _parse_ics_datetime(raw: str) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _empty_cal_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "ts", "source", "type", "text", "tags", "refs", "amount",
        "pii_level", "date", "year_week",
    ])


# ---------------------------------------------------------------------------
# ChatGPT / Claude export parser
# ---------------------------------------------------------------------------

def parse_chatgpt_export(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse a ChatGPT (or Claude) export into a conversations DataFrame.

    Accepts either a raw JSON file or a ZIP containing conversations.json.
    """
    if filename.lower().endswith(".zip"):
        return _parse_chatgpt_zip(file_bytes)
    return _parse_chatgpt_json(file_bytes)


def _parse_chatgpt_zip(file_bytes: bytes) -> pd.DataFrame:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            # Look for conversations.json inside the ZIP
            for name in zf.namelist():
                if name.endswith("conversations.json"):
                    data = zf.read(name)
                    return _parse_chatgpt_json(data)
            # Fallback: try first JSON file
            for name in zf.namelist():
                if name.endswith(".json"):
                    data = zf.read(name)
                    return _parse_chatgpt_json(data)
    except zipfile.BadZipFile:
        pass
    return _empty_conv_df()


def _parse_chatgpt_json(file_bytes: bytes) -> pd.DataFrame:
    try:
        raw = json.loads(file_bytes.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _empty_conv_df()

    rows: list[dict[str, Any]] = []

    # ChatGPT export format: list of conversation objects with "mapping" dict
    if isinstance(raw, list):
        for conv in raw:
            if not isinstance(conv, dict):
                continue
            conv_title = conv.get("title", "")
            create_time = conv.get("create_time")
            ts = _epoch_to_datetime(create_time)

            # Extract user messages from the mapping structure
            mapping = conv.get("mapping", {})
            if isinstance(mapping, dict):
                for node in mapping.values():
                    msg = node.get("message") if isinstance(node, dict) else None
                    if not isinstance(msg, dict):
                        continue
                    author = msg.get("author", {})
                    role = author.get("role", "") if isinstance(author, dict) else ""
                    if role != "user":
                        continue
                    content = msg.get("content", {})
                    parts = content.get("parts", []) if isinstance(content, dict) else []
                    text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
                    if not text:
                        continue
                    msg_ts = _epoch_to_datetime(msg.get("create_time")) or ts
                    rows.append({
                        "id": f"c_{len(rows):04d}",
                        "ts": msg_ts,
                        "source": "ai_chat",
                        "type": "conversation",
                        "text": text,
                        "tags": _infer_conversation_tags(text, conv_title),
                        "refs": [],
                        "amount": None,
                        "pii_level": "user_upload",
                    })

    if not rows:
        return _empty_conv_df()

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["date"] = df["ts"].dt.date
    iso = df["ts"].dt.isocalendar()
    df["year_week"] = (
        iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    )
    return df


def _epoch_to_datetime(epoch: Any) -> datetime | None:
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


_TAG_PATTERNS: dict[str, tuple[str, ...]] = {
    "anxiety": ("anxiety", "anxious", "nervous", "panic", "worried"),
    "stress": ("stress", "stressed", "pressure", "overwhelm"),
    "burnout": ("burnout", "exhausted", "burned out", "tired"),
    "money": ("money", "budget", "finance", "savings", "debt", "rent", "mortgage"),
    "career": ("career", "job", "promotion", "interview", "resume", "salary"),
    "health": ("health", "doctor", "sick", "exercise", "sleep", "therapy"),
    "relationship": ("relationship", "partner", "dating", "family", "friend"),
    "productivity": ("productivity", "procrastination", "focus", "adhd", "habit"),
}


def _infer_conversation_tags(text: str, title: str) -> list[str]:
    combined = f"{title} {text}".lower()
    tags: list[str] = []
    for tag, keywords in _TAG_PATTERNS.items():
        if any(kw in combined for kw in keywords):
            tags.append(tag)
    return tags


def _empty_conv_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "ts", "source", "type", "text", "tags", "refs", "amount",
        "pii_level", "date", "year_week",
    ])
