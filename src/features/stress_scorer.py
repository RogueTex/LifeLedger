from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

DEADLINE_KEYWORDS: tuple[str, ...] = (
    "review",
    "deadline",
    "performance",
    "promotion",
    "1:1",
    "okr",
    "presentation",
    "launch",
    "demo",
)


TEXT_COLUMNS_CANDIDATES: tuple[str, ...] = (
    "text",
    "title",
    "subject",
    "description",
    "summary",
    "notes",
    "event",
)


START_TS_CANDIDATES: tuple[str, ...] = ("start", "start_time", "start_ts", "ts", "timestamp", "datetime")
END_TS_CANDIDATES: tuple[str, ...] = ("end", "end_time", "end_ts", "finish", "stop")


def _first_present(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    available = set(columns)
    for col in candidates:
        if col in available:
            return col
    return None


def _get_text_series(df: pd.DataFrame) -> pd.Series:
    pieces: list[pd.Series] = []
    for col in TEXT_COLUMNS_CANDIDATES:
        if col in df.columns:
            pieces.append(df[col].fillna("").astype(str))
    if not pieces:
        return pd.Series([""] * len(df), index=df.index, dtype="string")
    out = pieces[0]
    for part in pieces[1:]:
        out = out + " " + part
    return out.str.lower()


def _compute_no_free_blocks_flag(df: pd.DataFrame, date_col: str) -> pd.Series:
    start_col = _first_present(df.columns, START_TS_CANDIDATES)
    end_col = _first_present(df.columns, END_TS_CANDIDATES)

    if start_col and end_col:
        start_ts = pd.to_datetime(df[start_col], errors="coerce", utc=True)
        end_ts = pd.to_datetime(df[end_col], errors="coerce", utc=True)
        duration_hours = (end_ts - start_ts).dt.total_seconds().div(3600).clip(lower=0).fillna(0.0)
        busy_hours = duration_hours.groupby(df[date_col]).sum()
        # Heuristic: a day with >= 7 busy hours likely has no meaningful free blocks.
        return (busy_hours >= 7.0).astype(int)

    meeting_count = df.groupby(date_col).size()
    # Fallback when event boundaries are missing.
    return (meeting_count >= 8).astype(int)


def compute_stress(calendar_df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily stress metrics from calendar events.

    Returns a dataframe with columns: date, stress_raw, stress_smooth.
    """
    if calendar_df is None or calendar_df.empty:
        return pd.DataFrame(columns=["date", "stress_raw", "stress_smooth"])

    df = calendar_df.copy()

    ts_col = _first_present(df.columns, START_TS_CANDIDATES)
    if ts_col is not None:
        df["ts"] = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    elif "date" in df.columns:
        df["ts"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    else:
        df["ts"] = pd.NaT

    df["date"] = df["ts"].dt.date
    df = df[df["date"].notna()].copy()

    if df.empty:
        return pd.DataFrame(columns=["date", "stress_raw", "stress_smooth"])

    text = _get_text_series(df)
    pattern = "|".join(map(re.escape, DEADLINE_KEYWORDS))
    df["deadline_hit"] = text.str.contains(pattern, na=False, regex=True)

    meeting_count = df.groupby("date").size().astype(float)
    deadline_flag = df.groupby("date")["deadline_hit"].any().astype(int)
    no_free_blocks_flag = _compute_no_free_blocks_flag(df, "date")

    daily = pd.DataFrame(index=meeting_count.index).sort_index()
    daily["meeting_count"] = meeting_count
    daily["deadline_keyword_flag"] = deadline_flag.reindex(daily.index).fillna(0).astype(float)
    daily["no_free_blocks_flag"] = no_free_blocks_flag.reindex(daily.index).fillna(0).astype(float)

    stress_linear = (
        daily["meeting_count"] * 0.4
        + daily["deadline_keyword_flag"] * 0.4
        + daily["no_free_blocks_flag"] * 0.2
    )

    min_v = float(stress_linear.min())
    max_v = float(stress_linear.max())
    if max_v > min_v:
        daily["stress_raw"] = (stress_linear - min_v) / (max_v - min_v)
    else:
        daily["stress_raw"] = 0.0

    daily["stress_smooth"] = daily["stress_raw"].rolling(window=7, min_periods=1).mean()

    out = daily.reset_index()[["date", "stress_raw", "stress_smooth"]]
    return out
