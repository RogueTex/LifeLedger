# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeLedger is a personal finance intelligence engine built for the **Data Portability Hackathon 2026, Track 3**. It ingests exported personal data (transactions, calendar, emails, AI conversations, lifelog) to surface behavioral patterns — the thesis being that financial behavior is driven by stress, emotional state, and calendar pressure.

**Tech stack:** Python 3.12, pandas, Streamlit, Plotly, GPT-4o-mini (narrative generation), rule-based + statistical features.

## Commands

```bash
# Run the Streamlit app
streamlit run src/ui/app.py

# Run tests (42 pytest cases)
pytest tests/test_features.py

# Run a single test
pytest tests/test_features.py::test_name -v

# Regenerate insight caches (required after feature/insight logic changes)
python3 -c "from src.insights.insight_engine import save_insights; save_insights('p01'); save_insights('p05')"

# Compile check all modules
python3 -m py_compile src/loaders/persona_loader.py src/loaders/upload_parser.py src/features/stress_scorer.py src/features/spend_tagger.py src/features/correlation.py src/features/resilience_model.py src/insights/insight_engine.py src/insights/narrative_gen.py src/ui/app.py

# Refresh demo backups
python3 scripts/generate_demo_backups.py

# Demo dry run checklist
./scripts/demo_dry_run.sh
```

## Architecture

### Data flow pipeline
```
data/raw/persona_pXX/*.jsonl
  → src/loaders/persona_loader.py (normalize → unified timeline DataFrame)
  → src/features/ (stress_scorer → spend_tagger → correlation → resilience_model)
  → src/insights/insight_engine.py (compute insights → validate schema → write JSON cache)
  → outputs/insights_pXX.json (frozen cache, used by UI)
  → src/ui/app.py (Streamlit dashboard reads cached insights)
  → src/insights/narrative_gen.py (GPT-4o-mini chat answers from cached insight JSON)
```

### Key modules

- **`src/loaders/persona_loader.py`** — Loads JSON/JSONL persona data, normalizes schemas, builds unified timeline with columns: `ts`, `date`, `week`, `year_week` (format: `YYYY-WW`), `tags`, `refs`, `amount`, `text`, `source`.
- **`src/loaders/upload_parser.py`** — Parses user-uploaded files: bank CSV (Chase/BofA/Amex/Mint), Google Calendar ICS, ChatGPT/Claude JSON/ZIP exports.
- **`src/features/stress_scorer.py`** — Calendar-derived daily stress scores with smoothing.
- **`src/features/spend_tagger.py`** — Discretionary spend tagging and weekly totals.
- **`src/features/correlation.py`** — Stress/spend correlation with spike week detection. Tests multiple alignments (same-week, prior-week) and selects strongest valid signal.
- **`src/features/resilience_model.py`** — Stability, volatility, runway, regret risk, macro-adjusted decomposition. Uses CPI YoY with fallback chain: provided series → local cache → FRED fetch → synthetic fallback.
- **`src/insights/insight_engine.py`** — End-to-end insight computation, schema validation (`v1_locked`), and cache writer. Theme extraction uses `THEME_LEXICON`.
- **`src/insights/narrative_gen.py`** — GPT-4o-mini narrative generation with retry/backoff (3 attempts), 12K char payload truncation, temp 0.3.
- **`src/ui/app.py`** — Streamlit dashboard: welcome gate, KPI cards, timeline chart, spike evidence cards, resilience panel with overlay toggles, grounded chat. CSS vars: `--bg`, `--card`, `--accent`, `--warn`, `--positive`.

### Personas used
- **p01 (Jordan Lee)** — Burnout + home savings. Primary demo: stress-spend correlation, goal velocity, anxiety themes.
- **p05 (Theo Nakamura)** — ADHD + freelance. Secondary demo: undercharging detection, invoice tracking, implied rate alert.

## Locked Contracts

### Loader contract
Top-level keys: `profile`, `consent`, `lifelog`, `conversations`, `emails`, `calendar`, `social_posts`, `transactions`, `files_index`. The `year_week` format is strictly `YYYY-WW`.

### Insight contract (`schema_version: v1_locked`)
Every insight row must include: `id`, `title`, `finding`, `evidence` (list), `dollar_impact`. Do not modify the schema without explicit versioning.

### Resilience insight IDs
`resilience_stability`, `resilience_volatility_index`, `resilience_liquidity_runway_forecast`, `resilience_regret_risk_signal`, `resilience_decomposition`.

## Important Conventions

- After changing feature or insight logic, always regenerate cached insights and verify with `pytest`.
- Frozen caches in `outputs/` are what the UI reads — the app does not recompute insights live for demo personas.
- Use `escape()` for user content in HTML within the Streamlit app.
- Environment requires `OPENAI_API_KEY` in `.env` for narrative chat (see `.env.example`).
- All persona data is 100% synthetic. Delete after March 31, 2026 per hackathon rules.
