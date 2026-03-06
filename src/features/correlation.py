from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def _parse_year_week(value: str | None) -> tuple[int, int] | None:
    if value is None or not isinstance(value, str) or "-" not in value:
        return None
    try:
        year_s, week_s = value.split("-", 1)
        return int(year_s), int(week_s)
    except ValueError:
        return None


def _prev_year_week(year_week: str | None) -> str | None:
    parsed = _parse_year_week(year_week)
    if parsed is None:
        return None
    year, week = parsed
    if week > 1:
        return f"{year}-{week - 1:02d}"
    prev_year = year - 1
    prev_year_weeks = int(pd.Timestamp(f"{prev_year}-12-28").isocalendar().week)
    return f"{prev_year}-{prev_year_weeks:02d}"


def _weekly_stress(stress_df: pd.DataFrame) -> pd.DataFrame:
    if stress_df is None or stress_df.empty:
        return pd.DataFrame(columns=["year_week", "weekly_stress_avg", "weekly_stress_raw_avg"])

    df = stress_df.copy()
    metric_col = "stress_smooth" if "stress_smooth" in df.columns else "stress_raw"
    raw_col = "stress_raw" if "stress_raw" in df.columns else metric_col

    if "year_week" not in df.columns:
        if "date" in df.columns:
            date_ts = pd.to_datetime(df["date"], errors="coerce", utc=True)
            iso = date_ts.dt.isocalendar()
            df["year_week"] = (
                iso.year.astype("Int64").astype("string")
                + "-"
                + iso.week.astype("Int64").astype("string").str.zfill(2)
            )
            df.loc[date_ts.isna(), "year_week"] = None
        else:
            return pd.DataFrame(columns=["year_week", "weekly_stress_avg"])

    out = (
        df.dropna(subset=["year_week"])
        .groupby("year_week", as_index=False)[[metric_col, raw_col]]
        .mean()
        .rename(columns={metric_col: "weekly_stress_avg", raw_col: "weekly_stress_raw_avg"})
        .sort_values("year_week")
        .reset_index(drop=True)
    )
    if "weekly_stress_raw_avg" not in out.columns:
        out["weekly_stress_raw_avg"] = out["weekly_stress_avg"]
    return out


def _top_week_transactions(transactions_df: pd.DataFrame, year_week: str, limit: int = 3) -> list[dict[str, Any]]:
    if transactions_df is None or transactions_df.empty:
        return []
    if "year_week" not in transactions_df.columns:
        return []

    week_rows = transactions_df.loc[transactions_df["year_week"] == year_week].copy()
    if week_rows.empty:
        return []
    if "is_discretionary" in week_rows.columns:
        week_rows = week_rows.loc[week_rows["is_discretionary"] == True]
    if week_rows.empty:
        return []

    amount = pd.to_numeric(week_rows.get("amount"), errors="coerce").fillna(0.0).abs()
    week_rows["_abs_amount"] = amount
    week_rows = week_rows.loc[week_rows["_abs_amount"] > 0].sort_values("_abs_amount", ascending=False).head(limit)

    out: list[dict[str, Any]] = []
    for _, row in week_rows.iterrows():
        tags = row.get("spend_tags")
        if not isinstance(tags, list):
            tags = row.get("tags")
        out.append(
            {
                "date": str(row.get("date")) if pd.notna(row.get("date")) else None,
                "merchant": row.get("merchant"),
                "text": str(row.get("text") or row.get("description") or row.get("merchant") or "Transaction"),
                "amount": round(float(row.get("_abs_amount", 0.0)), 2),
                "tags": tags if isinstance(tags, list) else [],
            }
        )
    return out


def _top_week_events(calendar_df: pd.DataFrame, year_week: str, limit: int = 3) -> list[dict[str, Any]]:
    if calendar_df is None or calendar_df.empty:
        return []
    if "year_week" not in calendar_df.columns:
        return []

    week_rows = calendar_df.loc[calendar_df["year_week"] == year_week].copy()
    if week_rows.empty:
        return []

    out: list[dict[str, Any]] = []
    for _, row in week_rows.head(limit).iterrows():
        out.append(
            {
                "date": str(row.get("date")) if pd.notna(row.get("date")) else None,
                "title": str(row.get("text") or row.get("title") or row.get("subject") or "Event"),
                "tags": row.get("tags") if isinstance(row.get("tags"), list) else [],
            }
        )
    return out


def _pearson_if_valid(x: pd.Series, y: pd.Series) -> tuple[float | None, float | None]:
    if len(x) < 2 or len(y) < 2:
        return None, None
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return None, None
    if float(x.var(ddof=0)) <= 1e-12 or float(y.var(ddof=0)) <= 1e-12:
        return None, None
    corr_coef, p_val = pearsonr(x, y)
    if np.isnan(corr_coef) or np.isnan(p_val):
        return None, None
    return float(corr_coef), float(p_val)


def compute_correlation(
    stress_df: pd.DataFrame,
    weekly_spend_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
) -> dict[str, Any]:
    """Compute stress-spend relationship and highlight likely stress-linked spend spikes."""
    weekly_stress = _weekly_stress(stress_df)

    spend = weekly_spend_df.copy() if weekly_spend_df is not None else pd.DataFrame()
    if spend.empty or "year_week" not in spend.columns or "weekly_discretionary_total" not in spend.columns:
        return {
            "correlation_coefficient": None,
            "p_value": None,
            "insufficient_variance": True,
            "interpretation": "Insufficient weekly discretionary spend data to estimate a stable relationship.",
            "suggestion": "Collect at least 4 weeks with discretionary purchases and calendar activity, then rerun.",
            "lag_used": None,
            "spike_weeks": [],
        }

    merged = (
        weekly_stress.merge(spend[["year_week", "weekly_discretionary_total"]], on="year_week", how="inner")
        .dropna(subset=["weekly_stress_avg", "weekly_discretionary_total"])
        .copy()
    )

    corr_coef: float | None = None
    p_val: float | None = None
    lag_used: str | None = None

    if len(merged) < 2:
        interpretation = "Insufficient overlap between weekly stress and discretionary spend for Pearson correlation."
        insufficient_variance = True
    else:
        lag0 = merged.copy()
        lag0_smooth_corr, lag0_smooth_p = _pearson_if_valid(
            lag0["weekly_stress_avg"].astype(float),
            lag0["weekly_discretionary_total"].astype(float),
        )
        lag0_raw_corr, lag0_raw_p = _pearson_if_valid(
            lag0["weekly_stress_raw_avg"].astype(float),
            lag0["weekly_discretionary_total"].astype(float),
        )

        lag1 = merged.copy()
        lag1["prior_week"] = lag1["year_week"].apply(_prev_year_week)
        stress_map = dict(zip(weekly_stress["year_week"], weekly_stress["weekly_stress_avg"]))
        lag1["prior_week_stress"] = lag1["prior_week"].map(stress_map)
        stress_raw_map = dict(zip(weekly_stress["year_week"], weekly_stress["weekly_stress_raw_avg"]))
        lag1["prior_week_stress_raw"] = lag1["prior_week"].map(stress_raw_map)
        lag1 = lag1.dropna(subset=["prior_week_stress", "prior_week_stress_raw"], how="all")
        lag1_smooth_corr, lag1_smooth_p = _pearson_if_valid(
            lag1["prior_week_stress"].astype(float),
            lag1["weekly_discretionary_total"].astype(float),
        )
        lag1_raw_corr, lag1_raw_p = _pearson_if_valid(
            lag1["prior_week_stress_raw"].astype(float),
            lag1["weekly_discretionary_total"].astype(float),
        )

        candidates: list[tuple[str, float, float]] = []
        if lag0_smooth_corr is not None and lag0_smooth_p is not None:
            candidates.append(("same_week_smooth", lag0_smooth_corr, lag0_smooth_p))
        if lag1_smooth_corr is not None and lag1_smooth_p is not None:
            candidates.append(("prior_week_stress_smooth", lag1_smooth_corr, lag1_smooth_p))
        if lag0_raw_corr is not None and lag0_raw_p is not None:
            candidates.append(("same_week_raw", lag0_raw_corr, lag0_raw_p))
        if lag1_raw_corr is not None and lag1_raw_p is not None:
            candidates.append(("prior_week_stress_raw", lag1_raw_corr, lag1_raw_p))

        if not candidates:
            insufficient_variance = True
            interpretation = "Correlation is undefined due to low variance in weekly stress or spend."
        else:
            lag_used, corr_coef, p_val = max(candidates, key=lambda row: abs(row[1]))
            insufficient_variance = False
            strength = (
                "strong"
                if abs(corr_coef) >= 0.7
                else "moderate"
                if abs(corr_coef) >= 0.4
                else "weak"
            )
            direction = "positive" if corr_coef >= 0 else "negative"
            significance = "statistically significant" if p_val < 0.05 else "not statistically significant"
            interpretation = (
                f"{strength.capitalize()} {direction} relationship between stress and discretionary spend "
                f"using `{lag_used}` alignment "
                f"({significance})."
            )

    spend_mean = float(spend["weekly_discretionary_total"].mean())
    spend_std = float(spend["weekly_discretionary_total"].std(ddof=0))
    spike_threshold = spend_mean + (1.5 * spend_std)
    relaxed_threshold = spend_mean + (1.0 * spend_std)
    stress_map = dict(zip(weekly_stress["year_week"], weekly_stress["weekly_stress_avg"]))
    has_spend_variance = bool(spend_std > 1e-9)
    spikes: list[dict[str, Any]] = []
    spend_sorted = spend.sort_values("weekly_discretionary_total", ascending=False).copy()

    def _maybe_add_spike(row: pd.Series, threshold_value: float, min_stress: float | None) -> bool:
        week = row["year_week"]
        weekly_total = float(row["weekly_discretionary_total"])
        if not np.isfinite(weekly_total) or weekly_total <= threshold_value:
            return False

        prior_week = _prev_year_week(week)
        prior_stress_value = stress_map.get(prior_week)
        if min_stress is not None:
            if prior_stress_value is None or float(prior_stress_value) < min_stress:
                return False

        top_txns = _top_week_transactions(transactions_df, week, limit=3)
        top_events = _top_week_events(calendar_df, week, limit=3)
        spike_payload = {
            "year_week": week,
            "weekly_discretionary_total": round(weekly_total, 2),
            "top_transactions": top_txns,
            "calendar_events": top_events,
            "threshold_math": {
                "week_spend": round(weekly_total, 2),
                "mean": round(spend_mean, 2),
                "std": round(spend_std, 2),
                "threshold": round(threshold_value, 2),
                "prior_week_stress": None if prior_stress_value is None else round(float(prior_stress_value), 3),
            },
            "prior_week": prior_week,
            "prior_week_stress": None if prior_stress_value is None else round(float(prior_stress_value), 3),
            "evidence": (
                f"Week {week} spend ${weekly_total:,.2f} crossed threshold ${threshold_value:,.2f}; "
                f"prior week stress was "
                f"{'N/A' if prior_stress_value is None else f'{float(prior_stress_value):.2f}'}."
            ),
        }
        spikes.append(spike_payload)
        return True

    for _, row in spend_sorted.iterrows():
        _maybe_add_spike(row, spike_threshold, min_stress=0.55)
        if len(spikes) == 3:
            break
    if not spikes:
        for _, row in spend_sorted.iterrows():
            _maybe_add_spike(row, relaxed_threshold, min_stress=0.45)
            if len(spikes) == 3:
                break
    if not spikes and has_spend_variance:
        for _, row in spend_sorted.iterrows():
            _maybe_add_spike(row, spend_mean, min_stress=None)
            if len(spikes) == 1:
                break

    suggestion = (
        "Track discretionary categories weekly and compare against stressful calendar periods."
        if not insufficient_variance
        else "Variance is too low for stable correlation; collect more varied weeks and rerun."
    )

    return {
        "correlation_coefficient": None if corr_coef is None else float(corr_coef),
        "p_value": None if p_val is None else float(p_val),
        "insufficient_variance": bool(insufficient_variance),
        "interpretation": interpretation,
        "suggestion": suggestion,
        "lag_used": lag_used,
        "spike_weeks": spikes,
    }
