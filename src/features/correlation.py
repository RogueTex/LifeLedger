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
        return pd.DataFrame(columns=["year_week", "weekly_stress_avg"])

    df = stress_df.copy()
    metric_col = "stress_smooth" if "stress_smooth" in df.columns else "stress_raw"

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
        .groupby("year_week", as_index=False)[metric_col]
        .mean()
        .rename(columns={metric_col: "weekly_stress_avg"})
        .sort_values("year_week")
        .reset_index(drop=True)
    )
    return out


def compute_correlation(
    stress_df: pd.DataFrame,
    weekly_spend_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
) -> dict[str, Any]:
    """Compute stress-spend relationship and highlight likely stress-linked spend spikes."""
    _ = transactions_df, calendar_df
    weekly_stress = _weekly_stress(stress_df)

    spend = weekly_spend_df.copy() if weekly_spend_df is not None else pd.DataFrame()
    if spend.empty or "year_week" not in spend.columns or "weekly_discretionary_total" not in spend.columns:
        return {
            "correlation_coefficient": None,
            "p_value": None,
            "interpretation": "Insufficient weekly discretionary spend data.",
            "spike_weeks": [],
        }

    merged = (
        weekly_stress.merge(spend[["year_week", "weekly_discretionary_total"]], on="year_week", how="inner")
        .dropna(subset=["weekly_stress_avg", "weekly_discretionary_total"])
        .copy()
    )

    if len(merged) < 2:
        corr_coef = None
        p_val = None
        interpretation = "Insufficient overlap between weekly stress and discretionary spend for Pearson correlation."
    else:
        corr_coef, p_val = pearsonr(merged["weekly_stress_avg"], merged["weekly_discretionary_total"])
        if np.isnan(corr_coef) or np.isnan(p_val):
            corr_coef = None
            p_val = None
            interpretation = "Correlation is undefined due to low variance in weekly series."
        else:
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
                f"{strength.capitalize()} {direction} relationship between weekly stress and discretionary spend "
                f"({significance})."
            )

    spend_mean = float(spend["weekly_discretionary_total"].mean())
    spend_std = float(spend["weekly_discretionary_total"].std(ddof=0))
    spike_threshold = spend_mean + (1.5 * spend_std)

    stress_map = dict(zip(weekly_stress["year_week"], weekly_stress["weekly_stress_avg"]))

    spikes: list[dict[str, Any]] = []
    for _, row in spend.sort_values("weekly_discretionary_total", ascending=False).iterrows():
        week = row["year_week"]
        weekly_total = float(row["weekly_discretionary_total"])
        if not np.isfinite(weekly_total) or weekly_total <= spike_threshold:
            continue

        prior_week = _prev_year_week(week)
        prior_stress = stress_map.get(prior_week)
        if prior_stress is None or float(prior_stress) <= 0.6:
            continue

        spikes.append(
            {
                "year_week": week,
                "weekly_discretionary_total": weekly_total,
                "spike_threshold": spike_threshold,
                "prior_week": prior_week,
                "prior_week_stress": float(prior_stress),
                "evidence": (
                    f"Spend {weekly_total:.2f} exceeded threshold {spike_threshold:.2f}; "
                    f"prior week stress ({prior_week}) was {float(prior_stress):.2f}."
                ),
            }
        )

        if len(spikes) == 3:
            break

    return {
        "correlation_coefficient": None if corr_coef is None else float(corr_coef),
        "p_value": None if p_val is None else float(p_val),
        "interpretation": interpretation,
        "spike_weeks": spikes,
    }
