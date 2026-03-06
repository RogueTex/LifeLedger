from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

DISCRETIONARY_TAGS: tuple[str, ...] = (
    "food_delivery",
    "dining",
    "entertainment",
    "shopping",
    "alcohol",
    "coffee",
    "subscriptions",
    "rideshare",
    "impulse",
)

KEYWORD_MAP: dict[str, tuple[str, ...]] = {
    "food_delivery": ("uber eats", "doordash", "grubhub", "postmates", "delivery"),
    "dining": ("restaurant", "diner", "bistro", "brunch", "dining"),
    "entertainment": ("movie", "cinema", "concert", "netflix", "spotify", "hulu", "game"),
    "shopping": ("amazon", "target", "walmart", "mall", "shop", "ikea"),
    "alcohol": ("bar", "pub", "liquor", "wine", "beer", "brewery"),
    "coffee": ("coffee", "starbucks", "cafe", "latte", "espresso"),
    "subscriptions": ("subscription", "monthly", "recurring", "prime", "membership"),
    "rideshare": ("uber", "lyft", "rideshare", "taxi"),
    "impulse": ("impulse", "flash sale", "limited offer", "buy now", "one-click"),
}

TEXT_COLUMNS_CANDIDATES: tuple[str, ...] = (
    "text",
    "description",
    "merchant",
    "vendor",
    "category",
    "memo",
    "notes",
)


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


def _build_year_week(df: pd.DataFrame) -> pd.Series:
    if "year_week" in df.columns:
        existing = df["year_week"].astype("string")
        return existing.where(existing.notna(), None).astype("object")

    ts_col = _first_present(df.columns, ("ts", "timestamp", "datetime", "date"))
    if ts_col is None:
        return pd.Series([None] * len(df), index=df.index, dtype="object")

    ts = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    iso = ts.dt.isocalendar()
    out = iso.year.astype("Int64").astype("string") + "-" + iso.week.astype("Int64").astype("string").str.zfill(2)
    out = out.astype("object")
    out[ts.isna()] = None
    return out


def tag_spend(transactions_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tag discretionary transactions and return weekly discretionary totals."""
    if transactions_df is None or transactions_df.empty:
        tagged_empty = pd.DataFrame(columns=["is_discretionary"])
        weekly_empty = pd.DataFrame(columns=["year_week", "weekly_discretionary_total"])
        return tagged_empty, weekly_empty

    tagged = transactions_df.copy()
    tagged["year_week"] = _build_year_week(tagged)

    text = _get_text_series(tagged)
    existing_tags = tagged.get("tags")
    if existing_tags is None:
        existing_tags = pd.Series([[] for _ in range(len(tagged))], index=tagged.index)
    existing_tags = existing_tags.apply(lambda v: [str(x).lower() for x in v] if isinstance(v, list) else [])

    tag_patterns = {
        tag: re.compile("|".join(re.escape(k) for k in keywords), flags=re.IGNORECASE)
        for tag, keywords in KEYWORD_MAP.items()
    }

    matched_tags: list[list[str]] = []
    for idx, row_text in text.items():
        hits = {tag for tag, pattern in tag_patterns.items() if pattern.search(row_text)}
        raw_tags = set(existing_tags.loc[idx])
        for discretionary_tag in DISCRETIONARY_TAGS:
            if discretionary_tag in raw_tags:
                hits.add(discretionary_tag)
        matched_tags.append(hits)

    tagged["spend_tags"] = [sorted(list(v)) for v in matched_tags]
    tagged["is_discretionary"] = tagged["spend_tags"].apply(bool)

    amount = pd.to_numeric(tagged.get("amount", 0.0), errors="coerce").fillna(0.0).abs()
    discretionary_amount = amount.where(tagged["is_discretionary"], 0.0).astype(float)

    weekly_summary = (
        pd.DataFrame({"year_week": tagged["year_week"], "discretionary_amount": discretionary_amount})
        .dropna(subset=["year_week"])
        .groupby("year_week", as_index=False)["discretionary_amount"]
        .sum()
        .rename(columns={"discretionary_amount": "weekly_discretionary_total"})
        .sort_values("year_week")
        .reset_index(drop=True)
    )

    return tagged, weekly_summary
