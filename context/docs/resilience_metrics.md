# Financial Resilience Metrics (v1)

## Where Metrics Are Computed
- Core formulas: `src/features/resilience_model.py` (`compute_resilience_metrics`)
- Insight wiring: `src/insights/insight_engine.py` (resilience insight IDs)
- UI overlays: `web/client/src/components/dashboard/ResiliencePanel.tsx`

## Formulas
- Volatility Index (0-100):
  - `0.50 * rolling_weekly_discretionary_CV_score`
  - `+ 0.25 * spike_frequency_score`
  - `+ 0.25 * spike_magnitude_score`
- Income Instability (0-100):
  - `0.45 * inflow_timing_irregularity_score`
  - `+ 0.55 * inflow_variance_score` (weekly/monthly)
- Structural Expense Load (0-100):
  - `fixed_commitments / median_monthly_inflow` -> normalized and clamped
- Liquidity Runway Forecast (days):
  - If balance available: `balance / net_burn_monthly * 30`
  - If balance unavailable: effective cadence runway from inflow rhythm vs fixed daily load
- Regret Risk Signal (0-100):
  - stress-amplified discretionary spending that occurs within `N` days before next inflow (`N=5` default)
- Stability Score (0-100):
  - baseline (no overlays): structural + income only
  - behavioral overlay: adds behavioral risk (`0.6*volatility + 0.4*regret`)
  - macro overlay: adds CPI-driven macro pressure
  - all scores normalized to `[0,100]`

## Decomposition
Percent contributions sum to ~100:
- behavioral
- structural fixed load
- income instability
- macro pressure

## Macro Overlay Source/Fallback
1. provided macro series
2. local cache `data/processed/cpi_yoy_cache.csv`
3. deterministic fetch from FRED CPIAUCSL
4. deterministic synthetic fallback

## Assumptions and Fallbacks
- Transaction amount sign conventions may be mixed; amounts are normalized to absolute values.
- Inflow detection uses tags/text keywords; when inflows are sparse, profile annual income proxy is used.
- If explicit balance is missing, runway becomes an effective cadence estimate (lower confidence).
- Macro pressure maps CPI YoY above 2% target into a 0-100 pressure score.
