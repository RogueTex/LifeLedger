from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


DATAFRAME_FILES = [
    "lifelog",
    "conversations",
    "emails",
    "calendar",
    "social_posts",
    "transactions",
    "files_index",
]

REQUIRED_COLUMNS = ["ts", "date", "week", "year_week", "tags", "refs", "amount", "text", "source"]
YEAR_WEEK_PATTERN = re.compile(r"^\d{4}-\d{2}$")
AMOUNT_IN_TEXT_PATTERN = re.compile(r"\$?\s*(-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|-?\d+(?:\.\d{1,2})?)")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _pick_ts_column(df: pd.DataFrame) -> pd.Series:
    candidates = [
        "ts",
        "timestamp",
        "datetime",
        "date",
        "time",
        "created_at",
        "updated_at",
        "start",
        "start_time",
    ]

    for col in candidates:
        if col in df.columns:
            ts = pd.to_datetime(df[col], errors="coerce", utc=True)
            if ts.notna().any():
                return ts

    return pd.to_datetime(pd.Series([pd.NaT] * len(df), index=df.index), utc=True)


def _extract_amount_from_text(text: Any) -> float | None:
    if text is None:
        return None
    match = AMOUNT_IN_TEXT_PATTERN.search(str(text))
    if not match:
        return None
    raw = match.group(1).replace(",", "").strip()
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _normalize_dataframe(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if df.empty:
        normalized = df.copy()
        for col in REQUIRED_COLUMNS:
            if col not in normalized.columns:
                normalized[col] = [] if col in {"tags", "refs"} else None
        return normalized

    normalized = df.copy()

    normalized["ts"] = _pick_ts_column(normalized)

    iso = normalized["ts"].dt.isocalendar()
    normalized["date"] = normalized["ts"].dt.date
    normalized["week"] = iso.week.astype("Int64")
    normalized["year_week"] = (
        iso.year.astype("Int64").astype("string") + "-" + iso.week.astype("Int64").astype("string").str.zfill(2)
    )
    normalized.loc[normalized["ts"].isna(), ["date", "week", "year_week"]] = None

    if "tags" in normalized.columns:
        normalized["tags"] = normalized["tags"].apply(_to_list)
    else:
        normalized["tags"] = [[] for _ in range(len(normalized))]

    if "refs" in normalized.columns:
        normalized["refs"] = normalized["refs"].apply(_to_list)
    else:
        normalized["refs"] = [[] for _ in range(len(normalized))]

    if "text" in normalized.columns:
        normalized["text"] = normalized["text"].fillna("").astype(str)
    else:
        normalized["text"] = ""

    if "amount" in normalized.columns:
        amount = pd.to_numeric(normalized["amount"], errors="coerce")
    else:
        amount = pd.Series([pd.NA] * len(normalized), index=normalized.index, dtype="Float64")
    inferred_amount = normalized["text"].apply(_extract_amount_from_text)
    amount = amount.where(amount.notna(), pd.to_numeric(inferred_amount, errors="coerce"))
    normalized["amount"] = amount.where(amount.notna(), None).astype(object)

    if "source" in normalized.columns:
        normalized["source"] = normalized["source"].fillna(source_name).astype(str)
    else:
        normalized["source"] = source_name

    valid_year_week = normalized["year_week"].isna() | normalized["year_week"].astype(str).str.match(YEAR_WEEK_PATTERN)
    if not bool(valid_year_week.all()):
        bad_examples = (
            normalized.loc[~valid_year_week, "year_week"].astype(str).dropna().head(3).tolist()
        )
        raise ValueError(f"Invalid year_week values for {source_name}: {bad_examples}")

    return normalized


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_json(path, lines=True)


def load_persona(persona_id: str) -> dict[str, Any]:
    persona_dir = _project_root() / "data" / "raw" / f"persona_{persona_id}"

    if not persona_dir.exists():
        raise FileNotFoundError(f"Persona directory not found: {persona_dir}")

    persona_data: dict[str, Any] = {
        "profile": _read_json(persona_dir / "persona_profile.json"),
        "consent": _read_json(persona_dir / "consent.json"),
    }

    for name in DATAFRAME_FILES:
        df = _read_jsonl(persona_dir / f"{name}.jsonl")
        persona_data[name] = _normalize_dataframe(df, source_name=name)

    expected_keys = {"profile", "consent", *DATAFRAME_FILES}
    actual_keys = set(persona_data.keys())
    if actual_keys != expected_keys:
        raise ValueError(f"Loader contract mismatch. expected={sorted(expected_keys)} actual={sorted(actual_keys)}")

    return persona_data


def build_timeline(persona_data: dict[str, Any]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for name, value in persona_data.items():
        if isinstance(value, pd.DataFrame):
            df = value.copy()
            if "source" not in df.columns:
                df["source"] = name
            frames.append(_normalize_dataframe(df, source_name=name))

    if not frames:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    timeline = pd.concat(frames, ignore_index=True, sort=False)
    timeline = timeline.sort_values("ts", ascending=True, na_position="last").reset_index(drop=True)
    return timeline
