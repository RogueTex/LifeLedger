from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

from .spend_tagger import tag_spend

INFLOW_KEYWORDS: tuple[str, ...] = (
    "income",
    "salary",
    "payroll",
    "paycheck",
    "deposit",
    "invoice",
    "revenue",
    "client payment",
    "transfer in",
    "refund",
    "bonus",
)

FIXED_LOAD_KEYWORDS: tuple[str, ...] = (
    "rent",
    "mortgage",
    "utilities",
    "insurance",
    "internet",
    "phone",
    "loan",
    "debt",
    "minimum payment",
    "subscription",
    "membership",
)

STRUCTURAL_LEVER_TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "id": "fixed_commitment_reduction",
        "title": "Lower fixed commitment burden",
        "why": "Fixed monthly obligations are consuming a high share of inflow.",
        "action": "Renegotiate or cancel one recurring commitment in the next 14 days.",
    },
    {
        "id": "inflow_smoothing",
        "title": "Smooth inflow timing",
        "why": "Income timing irregularity is widening cash-flow gaps.",
        "action": "Shift at least one invoice cadence to shorter cycles or add milestone billing.",
    },
    {
        "id": "pre_income_spend_guardrail",
        "title": "Add a pre-income spend guardrail",
        "why": "Discretionary spend clusters near income arrival windows.",
        "action": "Set a temporary discretionary cap for the 5 days before expected inflows.",
    },
    {
        "id": "volatility_smoothing",
        "title": "Smooth weekly discretionary spend",
        "why": "Weekly discretionary spend swings are driving stability loss.",
        "action": "Pre-allocate one fixed weekly discretionary budget envelope.",
    },
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, value)))


def _extract_profile_number(profile: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        raw = profile.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None


def _parse_income_approx(profile: dict[str, Any]) -> float | None:
    raw = str(profile.get("income_approx") or "").lower().replace(",", "")
    if not raw:
        return None
    tokens = [t for t in raw.replace("$", "").split() if any(ch.isdigit() for ch in t)]
    for token in tokens:
        cleaned = "".join(ch for ch in token if ch.isdigit() or ch == ".")
        if not cleaned:
            continue
        try:
            value = float(cleaned)
        except ValueError:
            continue
        if "k" in token:
            value *= 1000.0
        return value
    return None


def _to_year_week(dates: pd.Series) -> pd.Series:
    ts = pd.to_datetime(dates, errors="coerce", utc=True)
    iso = ts.dt.isocalendar()
    out = iso.year.astype("Int64").astype("string") + "-" + iso.week.astype("Int64").astype("string").str.zfill(2)
    out = out.astype("object")
    out[ts.isna()] = None
    return out


def _weekly_stress_series(stress_df: pd.DataFrame) -> pd.DataFrame:
    if stress_df is None or stress_df.empty:
        return pd.DataFrame(columns=["year_week", "weekly_stress"])

    df = stress_df.copy()
    metric_col = "stress_smooth" if "stress_smooth" in df.columns else "stress_raw"
    if "year_week" not in df.columns:
        if "date" in df.columns:
            df["year_week"] = _to_year_week(df["date"])
        else:
            return pd.DataFrame(columns=["year_week", "weekly_stress"])

    return (
        df.dropna(subset=["year_week"])
        .groupby("year_week", as_index=False)[metric_col]
        .mean()
        .rename(columns={metric_col: "weekly_stress"})
        .sort_values("year_week")
        .reset_index(drop=True)
    )


def _load_cpi_macro(macro_series: pd.DataFrame | None, min_date: pd.Timestamp | None, max_date: pd.Timestamp | None) -> tuple[pd.DataFrame, str]:
    """Return monthly CPI YoY (%) series and source label.

    Priority:
    1) caller-provided `macro_series` with columns like `date` + `cpi_yoy`
    2) local cache file `data/processed/cpi_yoy_cache.csv`
    3) deterministic fetch from FRED CPIAUCSL and derive YoY
    4) deterministic synthetic fallback if fetch/cache are unavailable
    """
    if isinstance(macro_series, pd.DataFrame) and not macro_series.empty:
        df = macro_series.copy()
        if "date" not in df.columns:
            if "ts" in df.columns:
                df["date"] = df["ts"]
            else:
                return pd.DataFrame(columns=["date", "cpi_yoy"]), "none"
        if "cpi_yoy" not in df.columns:
            for candidate in ("value", "macro_value", "cpi", "inflation_yoy"):
                if candidate in df.columns:
                    df["cpi_yoy"] = pd.to_numeric(df[candidate], errors="coerce")
                    break
        if "cpi_yoy" in df.columns:
            out = df[["date", "cpi_yoy"]].copy()
            out["date"] = pd.to_datetime(out["date"], errors="coerce", utc=True)
            out["cpi_yoy"] = pd.to_numeric(out["cpi_yoy"], errors="coerce")
            out = out.dropna(subset=["date", "cpi_yoy"]).sort_values("date").reset_index(drop=True)
            if not out.empty:
                return out, "provided_series"

    processed_dir = _project_root() / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    cache_path = processed_dir / "cpi_yoy_cache.csv"

    if cache_path.exists():
        try:
            cached = pd.read_csv(cache_path)
            cached["date"] = pd.to_datetime(cached.get("date"), errors="coerce", utc=True)
            cached["cpi_yoy"] = pd.to_numeric(cached.get("cpi_yoy"), errors="coerce")
            cached = cached.dropna(subset=["date", "cpi_yoy"]).sort_values("date")
            if not cached.empty:
                return cached[["date", "cpi_yoy"]].reset_index(drop=True), "cache"
        except Exception:
            pass

    fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
    try:
        with urlopen(fred_url, timeout=6) as response:
            raw = response.read().decode("utf-8")
        fetched = pd.read_csv(io.StringIO(raw))
        fetched.columns = [c.strip().lower() for c in fetched.columns]
        if "date" in fetched.columns and "cpiaucsl" in fetched.columns:
            fetched["date"] = pd.to_datetime(fetched["date"], errors="coerce", utc=True)
            fetched["cpiaucsl"] = pd.to_numeric(fetched["cpiaucsl"], errors="coerce")
            fetched = fetched.dropna(subset=["date", "cpiaucsl"]).sort_values("date")
            fetched["cpi_yoy"] = fetched["cpiaucsl"].pct_change(periods=12) * 100.0
            out = fetched[["date", "cpi_yoy"]].dropna().reset_index(drop=True)
            if not out.empty:
                out.to_csv(cache_path, index=False)
                return out, "fred_live"
    except (URLError, TimeoutError, OSError, ValueError):
        pass

    # Deterministic fallback anchored to observed date range.
    anchor_start = min_date or pd.Timestamp("2024-01-01", tz="UTC")
    anchor_end = max_date or pd.Timestamp("2025-12-31", tz="UTC")
    month_idx = pd.date_range(anchor_start.floor("D"), anchor_end.ceil("D"), freq="MS", tz="UTC")
    values = []
    for i, _dt in enumerate(month_idx):
        # Smooth and deterministic synthetic inflation regime around 2.4% to 3.6%.
        value = 3.0 + 0.6 * math.sin((i + 2) / 4.0) - 0.2 * math.cos((i + 1) / 6.0)
        values.append(round(value, 3))
    out = pd.DataFrame({"date": month_idx, "cpi_yoy": values})
    return out, "deterministic_fallback"


def _macro_pressure_score(cpi_yoy: float | None) -> float:
    if cpi_yoy is None:
        return 0.0
    # 2.0% is considered neutral; 6.0% maps to near-max pressure.
    scaled = ((float(cpi_yoy) - 2.0) / 4.0) * 100.0
    return _clamp(scaled)


def _compute_next_inflow_days(discretionary_dates: pd.Series, inflow_dates: pd.Series) -> pd.Series:
    if discretionary_dates.empty or inflow_dates.empty:
        return pd.Series([pd.NA] * len(discretionary_dates), index=discretionary_dates.index, dtype="Float64")

    inflow_sorted = pd.to_datetime(inflow_dates, errors="coerce", utc=True).dropna().sort_values().to_list()
    if not inflow_sorted:
        return pd.Series([pd.NA] * len(discretionary_dates), index=discretionary_dates.index, dtype="Float64")

    out: list[float | None] = []
    for dt in pd.to_datetime(discretionary_dates, errors="coerce", utc=True):
        if pd.isna(dt):
            out.append(None)
            continue
        days = None
        for inflow in inflow_sorted:
            delta = (inflow - dt).days
            if delta >= 0:
                days = float(delta)
                break
        out.append(days)
    return pd.Series(out, index=discretionary_dates.index, dtype="Float64")


def compute_resilience_metrics(
    transactions_df: pd.DataFrame,
    weekly_stress_series: pd.DataFrame,
    macro_series: pd.DataFrame | None = None,
    profile: dict[str, Any] | None = None,
    pre_income_window_days: int = 5,
) -> dict[str, Any]:
    """Compute financial resilience metrics from normalized transactions and stress.

    Metric definitions implemented in this function:
    - Volatility Index (0-100): weighted blend of rolling weekly discretionary CV,
      discretionary spike frequency, and spike magnitude.
    - Income Instability (0-100): inflow timing irregularity + inflow variance.
    - Structural Expense Load (0-100): fixed commitments / median monthly inflow.
    - Liquidity Runway Forecast (days): net burn estimate and effective runway fallback
      when balance is unavailable.
    - Regret Risk Signal (0-100): stress-amplified discretionary spending in the
      N-day pre-income window.
    - Stability Score (0-100): inverse weighted instability; also emits with/without
      macro overlay and decomposition percentages.
    """
    profile = profile or {}

    tx = transactions_df.copy() if transactions_df is not None else pd.DataFrame()
    if tx.empty:
        return {
            "model_version": "resilience_v1",
            "stability_score": 50.0,
            "stability_score_with_macro": 50.0,
            "volatility_index": 50.0,
            "income_instability": 50.0,
            "structural_expense_load": 50.0,
            "liquidity_runway_days": None,
            "liquidity_runway_confidence": {"low": None, "high": None, "confidence": "low"},
            "regret_risk_signal": 50.0,
            "macro_pressure": 0.0,
            "macro_context": {"source": "none", "latest_cpi_yoy": None},
            "decomposition_percentages": {
                "behavioral": 25.0,
                "structural_fixed_load": 25.0,
                "income_instability": 25.0,
                "macro_pressure": 25.0,
            },
            "component_scores": {
                "behavioral_risk": 50.0,
                "structural_fixed_load": 50.0,
                "income_instability": 50.0,
                "macro_pressure": 0.0,
            },
            "model_weights": {"behavioral": 0.42, "structural": 0.33, "income": 0.25, "macro": 0.15},
            "overlay_scores": {
                "baseline_without_overlays": 50.0,
                "with_behavioral_only": 50.0,
                "with_macro_only": 50.0,
                "with_behavioral_and_macro": 50.0,
            },
            "explainers": {
                "stability": "Insufficient transaction data; returned neutral defaults.",
                "volatility": "Insufficient transaction data.",
                "liquidity": "Insufficient transaction data.",
                "regret": "Insufficient transaction data.",
            },
            "top_structural_levers": [dict(STRUCTURAL_LEVER_TEMPLATES[0]), dict(STRUCTURAL_LEVER_TEMPLATES[1]), dict(STRUCTURAL_LEVER_TEMPLATES[2])],
        }

    tx["amount"] = pd.to_numeric(tx.get("amount"), errors="coerce").abs().fillna(0.0)
    if "date" not in tx.columns:
        tx["date"] = pd.to_datetime(tx.get("ts"), errors="coerce", utc=True)
    else:
        tx["date"] = pd.to_datetime(tx["date"], errors="coerce", utc=True)
    if "year_week" not in tx.columns:
        tx["year_week"] = _to_year_week(tx["date"])
    tx["text_l"] = tx.get("text", "").fillna("").astype(str).str.lower()

    tag_values = tx.get("tags", pd.Series([[] for _ in range(len(tx))], index=tx.index))
    tx["tags_l"] = tag_values.apply(lambda v: [str(x).lower() for x in v] if isinstance(v, list) else [])

    tagged, weekly_discretionary = tag_spend(tx)
    if "is_discretionary" in tagged.columns:
        tx["is_discretionary"] = tagged["is_discretionary"].reindex(tx.index).fillna(False).astype(bool)
    else:
        tx["is_discretionary"] = False

    inflow_mask = tx["text_l"].str.contains("|".join(INFLOW_KEYWORDS), regex=True, na=False) | tx["tags_l"].apply(
        lambda tags: any(any(key in tag for key in INFLOW_KEYWORDS) for tag in tags)
    )

    fixed_mask = tx["text_l"].str.contains("|".join(FIXED_LOAD_KEYWORDS), regex=True, na=False) | tx["tags_l"].apply(
        lambda tags: any(any(key in tag for key in FIXED_LOAD_KEYWORDS) for tag in tags)
    )
    fixed_mask = fixed_mask & (~inflow_mask)

    tx["is_inflow"] = inflow_mask
    tx["is_fixed"] = fixed_mask

    weekly_stress = _weekly_stress_series(weekly_stress_series)

    # Volatility Index = rolling discretionary CV + spike frequency + spike magnitude.
    weekly_disc = weekly_discretionary.copy()
    if weekly_disc.empty:
        weekly_disc = pd.DataFrame(columns=["year_week", "weekly_discretionary_total"])
    weekly_disc["weekly_discretionary_total"] = pd.to_numeric(
        weekly_disc.get("weekly_discretionary_total"), errors="coerce"
    ).fillna(0.0)
    weekly_disc = weekly_disc.sort_values("year_week").reset_index(drop=True)

    roll_mean = weekly_disc["weekly_discretionary_total"].rolling(window=6, min_periods=3).mean()
    roll_std = weekly_disc["weekly_discretionary_total"].rolling(window=6, min_periods=3).std(ddof=0)
    cv_series = (roll_std / roll_mean.where(roll_mean > 1e-9)).replace([float("inf"), -float("inf")], pd.NA).dropna()
    cv_level = float(cv_series.median()) if not cv_series.empty else 0.0

    disc_mean = float(weekly_disc["weekly_discretionary_total"].mean()) if not weekly_disc.empty else 0.0
    disc_std = float(weekly_disc["weekly_discretionary_total"].std(ddof=0)) if not weekly_disc.empty else 0.0
    spike_threshold = disc_mean + disc_std
    spikes = weekly_disc.loc[weekly_disc["weekly_discretionary_total"] > spike_threshold, "weekly_discretionary_total"]
    spike_frequency = float(len(spikes)) / float(len(weekly_disc)) if len(weekly_disc) else 0.0
    spike_magnitude = float(((spikes - disc_mean) / max(disc_mean, 1.0)).mean()) if not spikes.empty else 0.0

    cv_score = _clamp((cv_level / 1.2) * 100.0)
    spike_freq_score = _clamp((spike_frequency / 0.35) * 100.0)
    spike_mag_score = _clamp((spike_magnitude / 2.0) * 100.0)
    volatility_index = _clamp(0.5 * cv_score + 0.25 * spike_freq_score + 0.25 * spike_mag_score)

    # Income instability = inflow timing irregularity + inflow variance (weekly/monthly).
    inflows = tx.loc[tx["is_inflow"]].copy()
    inflows = inflows.sort_values("date")

    timing_irregularity_score = 55.0
    inflow_variance_score = 55.0
    inflow_monthly_median = None
    median_inflow_gap_days = None

    if not inflows.empty:
        inflow_dates = inflows["date"].dropna()
        gap_days = inflow_dates.diff().dt.days.dropna()
        if not gap_days.empty:
            gap_median = float(gap_days.median())
            gap_std = float(gap_days.std(ddof=0))
            irregularity = gap_std / max(gap_median, 1.0)
            timing_irregularity_score = _clamp(irregularity * 100.0)
            median_inflow_gap_days = gap_median

        weekly_inflows = (
            inflows.dropna(subset=["year_week"]).groupby("year_week", as_index=False)["amount"].sum().rename(columns={"amount": "weekly_inflow"})
        )
        monthly_inflows = (
            inflows.assign(year_month=inflows["date"].dt.tz_localize(None).dt.to_period("M").astype(str))
            .groupby("year_month", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "monthly_inflow"})
        )
        cv_w = float(weekly_inflows["weekly_inflow"].std(ddof=0) / max(weekly_inflows["weekly_inflow"].mean(), 1.0)) if len(weekly_inflows) > 1 else 0.0
        cv_m = float(monthly_inflows["monthly_inflow"].std(ddof=0) / max(monthly_inflows["monthly_inflow"].mean(), 1.0)) if len(monthly_inflows) > 1 else 0.0
        inflow_variance_score = _clamp(((cv_w + cv_m) / 2.0) * 100.0)
        inflow_monthly_median = float(monthly_inflows["monthly_inflow"].median()) if not monthly_inflows.empty else None
    else:
        annual_income = _extract_profile_number(profile, "annual_income", "yearly_income", "income_yearly")
        if annual_income is None:
            annual_income = _parse_income_approx(profile)
        if annual_income is not None and annual_income > 0:
            inflow_monthly_median = annual_income / 12.0
            timing_irregularity_score = 45.0
            inflow_variance_score = 50.0

    income_instability = _clamp(0.45 * timing_irregularity_score + 0.55 * inflow_variance_score)

    # Structural expense load = fixed commitments / median inflow.
    fixed_monthly = 0.0
    fixed_tx = tx.loc[tx["is_fixed"]].copy()
    if not fixed_tx.empty:
        fixed_monthly_series = (
            fixed_tx.assign(year_month=fixed_tx["date"].dt.tz_localize(None).dt.to_period("M").astype(str))
            .groupby("year_month")["amount"]
            .sum()
        )
        fixed_monthly = float(fixed_monthly_series.mean()) if not fixed_monthly_series.empty else 0.0

    if inflow_monthly_median is None or inflow_monthly_median <= 0:
        annual_income = _extract_profile_number(profile, "annual_income", "yearly_income", "income_yearly")
        if annual_income is None:
            annual_income = _parse_income_approx(profile)
        if annual_income is not None and annual_income > 0:
            inflow_monthly_median = annual_income / 12.0

    load_ratio = fixed_monthly / max(inflow_monthly_median or 1.0, 1.0)
    structural_expense_load = _clamp((load_ratio / 0.8) * 100.0)

    # Liquidity runway and confidence band.
    non_inflow = tx.loc[~tx["is_inflow"]].copy()
    monthly_outflow = (
        non_inflow.assign(year_month=non_inflow["date"].dt.tz_localize(None).dt.to_period("M").astype(str))
        .groupby("year_month")["amount"]
        .sum()
    )
    avg_monthly_outflow = float(monthly_outflow.mean()) if not monthly_outflow.empty else 0.0
    monthly_inflow_proxy = float(inflow_monthly_median or 0.0)
    net_burn_monthly = max(0.0, avg_monthly_outflow - monthly_inflow_proxy)

    balance = _extract_profile_number(
        profile,
        "current_savings",
        "cash_balance",
        "checking_balance",
        "liquid_cash",
        "emergency_fund",
    )

    runway_mode = "balance_based" if balance and balance > 0 else "effective_cadence"
    if balance and balance > 0 and net_burn_monthly > 1e-9:
        runway_days = (balance / net_burn_monthly) * 30.0
    elif balance and balance > 0:
        runway_days = 365.0
    else:
        median_inflow_amount = float(inflows["amount"].median()) if not inflows.empty else monthly_inflow_proxy / 2.0
        if median_inflow_gap_days is None or median_inflow_gap_days <= 0:
            median_inflow_gap_days = 14.0
        fixed_daily = fixed_monthly / 30.0 if fixed_monthly > 0 else (avg_monthly_outflow / 30.0 if avg_monthly_outflow > 0 else 20.0)
        coverage_days = median_inflow_amount / max(fixed_daily, 1.0)
        cadence_factor = median_inflow_gap_days / 14.0
        runway_days = max(7.0, coverage_days * cadence_factor)

    uncertainty = _clamp((volatility_index * 0.5 + income_instability * 0.5), 0.0, 100.0) / 100.0
    band_width = runway_days * (0.2 + 0.35 * uncertainty)
    runway_low = max(0.0, runway_days - band_width)
    runway_high = runway_days + band_width
    confidence_label = "high" if uncertainty < 0.35 else "medium" if uncertainty < 0.65 else "low"

    # Regret Risk Signal = stress-amplified discretionary spend near pre-income windows.
    disc_tx = tx.loc[tx["is_discretionary"]].copy()
    if disc_tx.empty:
        regret_risk_signal = 0.0
        near_window_count = 0
        pre_income_ratio = 0.0
    else:
        if weekly_stress.empty:
            weekly_stress_map: dict[str, float] = {}
        else:
            weekly_stress_map = {
                str(k): float(v)
                for k, v in zip(weekly_stress["year_week"], pd.to_numeric(weekly_stress["weekly_stress"], errors="coerce").fillna(0.0))
            }

        disc_tx["days_to_next_inflow"] = _compute_next_inflow_days(disc_tx["date"], inflows["date"])
        disc_tx["week_stress"] = disc_tx["year_week"].map(weekly_stress_map).fillna(0.0)

        near_mask = disc_tx["days_to_next_inflow"].notna() & (disc_tx["days_to_next_inflow"] <= pre_income_window_days)
        near_window = disc_tx.loc[near_mask].copy()

        weighted_total = float((disc_tx["amount"] * (1.0 + 0.6 * disc_tx["week_stress"])).sum())
        weighted_near = float((near_window["amount"] * (1.0 + 0.6 * near_window["week_stress"])).sum())
        pre_income_ratio = weighted_near / max(weighted_total, 1.0)

        avg_days = float(near_window["days_to_next_inflow"].mean()) if not near_window.empty else float(pre_income_window_days)
        proximity = max(0.0, 1.0 - (avg_days / max(float(pre_income_window_days), 1.0)))
        stress_amp = 1.0 + 0.4 * float(near_window["week_stress"].mean()) if not near_window.empty else 1.0
        regret_raw = (0.6 * pre_income_ratio + 0.4 * proximity) * 100.0 * stress_amp
        regret_risk_signal = _clamp(regret_raw)
        near_window_count = int(len(near_window))

    # Macro pressure via CPI YoY.
    date_min = tx["date"].min() if tx["date"].notna().any() else None
    date_max = tx["date"].max() if tx["date"].notna().any() else None
    macro_df, macro_source = _load_cpi_macro(macro_series, date_min, date_max)
    latest_cpi_yoy = float(macro_df["cpi_yoy"].iloc[-1]) if not macro_df.empty else None
    macro_pressure = _macro_pressure_score(latest_cpi_yoy)

    behavioral_risk = _clamp(0.6 * volatility_index + 0.4 * regret_risk_signal)

    weights = {"behavioral": 0.42, "structural": 0.33, "income": 0.25, "macro": 0.15}

    baseline_risk = (
        weights["behavioral"] * behavioral_risk
        + weights["structural"] * structural_expense_load
        + weights["income"] * income_instability
    )
    with_behavioral_only_score = _clamp(100.0 - baseline_risk)

    no_overlay_risk = (
        weights["structural"] * structural_expense_load
        + weights["income"] * income_instability
    )
    baseline_without_overlays = _clamp(100.0 - no_overlay_risk)

    with_macro_only_risk = no_overlay_risk + weights["macro"] * macro_pressure
    with_macro_only_score = _clamp(100.0 - with_macro_only_risk)

    adjusted_risk = baseline_risk + weights["macro"] * macro_pressure
    adjusted_stability = _clamp(100.0 - adjusted_risk)

    contributions = {
        "behavioral": weights["behavioral"] * behavioral_risk,
        "structural_fixed_load": weights["structural"] * structural_expense_load,
        "income_instability": weights["income"] * income_instability,
        "macro_pressure": weights["macro"] * macro_pressure,
    }
    contribution_sum = max(sum(contributions.values()), 1e-9)
    decomposition_percentages = {
        key: round((value / contribution_sum) * 100.0, 2) for key, value in contributions.items()
    }

    lever_scores = {
        "fixed_commitment_reduction": structural_expense_load,
        "inflow_smoothing": income_instability,
        "pre_income_spend_guardrail": regret_risk_signal,
        "volatility_smoothing": volatility_index,
    }
    sorted_lever_ids = sorted(lever_scores.keys(), key=lambda key: lever_scores[key], reverse=True)[:3]
    top_levers = [next(item for item in STRUCTURAL_LEVER_TEMPLATES if item["id"] == lever_id) for lever_id in sorted_lever_ids]

    return {
        "model_version": "resilience_v1",
        "stability_score": round(with_behavioral_only_score, 2),
        "stability_score_with_macro": round(adjusted_stability, 2),
        "volatility_index": round(volatility_index, 2),
        "income_instability": round(income_instability, 2),
        "structural_expense_load": round(structural_expense_load, 2),
        "liquidity_runway_days": round(runway_days, 1),
        "liquidity_runway_confidence": {
            "low": round(runway_low, 1),
            "high": round(runway_high, 1),
            "confidence": confidence_label,
        },
        "liquidity_runway_mode": runway_mode,
        "net_burn_monthly": round(net_burn_monthly, 2),
        "regret_risk_signal": round(regret_risk_signal, 2),
        "regret_window_days": int(pre_income_window_days),
        "regret_near_window_count": near_window_count,
        "regret_pre_income_ratio": round(pre_income_ratio, 4),
        "macro_pressure": round(macro_pressure, 2),
        "macro_context": {
            "source": macro_source,
            "latest_cpi_yoy": None if latest_cpi_yoy is None else round(latest_cpi_yoy, 3),
            "target_yoy_reference": 2.0,
        },
        "decomposition_percentages": decomposition_percentages,
        "component_scores": {
            "behavioral_risk": round(behavioral_risk, 2),
            "structural_fixed_load": round(structural_expense_load, 2),
            "income_instability": round(income_instability, 2),
            "macro_pressure": round(macro_pressure, 2),
        },
        "model_weights": {
            "behavioral": weights["behavioral"],
            "structural": weights["structural"],
            "income": weights["income"],
            "macro": weights["macro"],
        },
        "overlay_scores": {
            "baseline_without_overlays": round(baseline_without_overlays, 2),
            "with_behavioral_only": round(with_behavioral_only_score, 2),
            "with_macro_only": round(with_macro_only_score, 2),
            "with_behavioral_and_macro": round(adjusted_stability, 2),
        },
        "explainers": {
            "stability": "Stability = 100 - weighted instability components, clamped to [0,100].",
            "volatility": "Volatility combines rolling weekly discretionary CV, spike frequency, and spike magnitude.",
            "liquidity": "Runway uses net burn when balance exists; otherwise effective cadence runway from inflow rhythm vs fixed obligations.",
            "regret": "Regret risk increases when discretionary spend clusters in the N-day pre-income window during elevated stress.",
            "income_instability": "Income instability blends inflow gap irregularity and inflow variance across weekly/monthly buckets.",
            "structural_expense_load": "Structural load is fixed commitments divided by median monthly inflow.",
        },
        "top_structural_levers": top_levers,
    }
