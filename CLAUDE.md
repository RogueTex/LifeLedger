# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeLedger is a personal finance intelligence engine built for the **Data Portability Hackathon 2026, Track 3**. It fuses exported personal data (transactions, calendar, emails, AI conversations, lifelog) to surface behavioral patterns invisible in any single source — the thesis being that financial behavior is driven by stress, emotional state, and calendar pressure.

**Tech stack:** Python 3.12, pandas, React 19 + TypeScript + Vite, Express 5, Recharts, Tailwind CSS, Framer Motion, narrative generation (Groq/OpenRouter/OpenAI via BYOK or `.env`), rule-based + statistical features.

## Commands

```bash
# Run the React web app (dev mode) — must start as TWO SEPARATE processes
# Terminal 1: API server
cd web && npx tsx server/index.ts
# Terminal 2: Vite frontend
cd web && npx vite --host
# API runs on :5000, frontend on :5173. Vite proxies /api to :5000.
# IMPORTANT: Do NOT combine these with bash `&` — they must be separate processes or Vite returns 404.

# TypeScript type check (React app)
cd web && npx tsc --noEmit

# Run tests (42 pytest cases)
pytest tests/test_features.py

# Run a single test
pytest tests/test_features.py::test_name -v

# Compile check all modules
python -m py_compile src/loaders/persona_loader.py src/loaders/upload_parser.py src/features/stress_scorer.py src/features/spend_tagger.py src/features/correlation.py src/features/resilience_model.py src/insights/insight_engine.py src/insights/narrative_gen.py

# Regenerate insight caches (required after feature/insight logic changes — needs persona data in data/raw/)
python -c "from src.insights.insight_engine import save_insights; save_insights('p01'); save_insights('p05')"

# Start web app
cd web && npm run dev
```

## Architecture

### Data flow pipeline
```
Demo personas (frozen caches):
  outputs/insights_pXX.json → GET /api/insights/:id → React dashboard renders

User uploads (live compute):
  web/client/src/components/dashboard/DataUploadSection.tsx (file selection + drag-drop)
    → POST /api/upload (base64 JSON payload, no multer)
    → scripts/process_upload.py (stdin JSON → upload_parser → compute_insights_from_dataframes)
    → insight JSON returned to client → dashboard renders

AI chat (BYOK supported):
  GroundedChat/GroundedChatUpload → POST /api/chat or /api/chat/upload
    → server passes BYOK key as env var override → narrative_gen.py
    → chat grounded strictly in precomputed insight JSON (never raw data)
```

### Key modules

- **`src/loaders/persona_loader.py`** — Loads JSON/JSONL persona data, normalizes schemas, builds unified timeline with columns: `ts`, `date`, `week`, `year_week` (format: `YYYY-WW`), `tags`, `refs`, `amount`, `text`, `source`.
- **`src/loaders/upload_parser.py`** — Parses user-uploaded files: bank CSV (Chase/BofA/Amex/Mint/Discover), Google Calendar ICS, ChatGPT/Claude JSON/ZIP exports.
- **`src/features/stress_scorer.py`** — Calendar-derived daily stress scores with smoothing.
- **`src/features/spend_tagger.py`** — 9-category discretionary spend tagging and weekly totals.
- **`src/features/correlation.py`** — Stress/spend correlation with 4-alignment testing and 3-tier spike detection.
- **`src/features/resilience_model.py`** — (Legacy, no longer used by insight engine.)
- **`src/insights/insight_engine.py`** — End-to-end insight computation (10 insight types for uploads, 7+1 for personas), schema validation (`v1_locked`), and cache writer. `compute_insights_from_dataframes()` runs the full pipeline on raw DataFrames.
- **`src/insights/narrative_gen.py`** — Narrative generation with retry/backoff (3 attempts), 12K char payload truncation, temp 0.3. Checks `GROQ_API_KEY` → `OPENROUTER_API_KEY` → `OPENAI_API_KEY` in priority order.
- **`web/server/index.ts`** — Express API: `/api/personas`, `/api/insights/:id`, `/api/chat`, `/api/upload`, `/api/chat/upload`. Supports BYOK keys via `byoKeyEnv()` helper.
- **`web/client/src/`** — React SPA: Welcome → Dashboard (demo personas) or YourData (user uploads). Uses wouter routing, TanStack Query, Recharts, Framer Motion.
- **`scripts/process_upload.py`** — Bridge script: reads base64 file payload from stdin, parses via `upload_parser`, runs `compute_insights_from_dataframes`, outputs JSON.

### Insight IDs (all data-contingent — only render when data supports them)

**Core (all personas + uploads):**
`stress_spend_correlation`, `top_anxiety_themes`, `months_to_goal`, `subscription_creep`, `expensive_day_of_week`, `post_payday_surge`, `worry_timeline`

**Upload-only (require cross-source data):**
`stress_category_shift` (calendar + transactions), `spending_velocity` (transactions with paydays), `recovery_spending` (calendar + transactions, 6+ weeks)

**Persona-specific:**
`invoice_rate_risk` (p05 only — emails + calendar)

### Personas used
- **p01 (Jordan Lee)** — Burnout + home savings. Primary demo: stress-spend correlation, goal velocity, anxiety themes.
- **p05 (Theo Nakamura)** — ADHD + freelance. Secondary demo: undercharging detection, invoice tracking, implied rate alert.

## Locked Contracts

### Loader contract
Top-level keys: `profile`, `consent`, `lifelog`, `conversations`, `emails`, `calendar`, `social_posts`, `transactions`, `files_index`. The `year_week` format is strictly `YYYY-WW`.

### Insight contract (`schema_version: v1_locked`)
Every insight row must include: `id`, `title`, `finding`, `evidence` (list), `dollar_impact`. New insights add `has_data` (boolean) for conditional rendering. Do not modify the schema without explicit versioning.

## UX & Content Rules

### No slop — only show what the data supports
- **Never render an insight card, chart, or KPI if the underlying data is empty or insufficient.** If there are no subscriptions, don't show the subscription panel. If there's no stress-spend correlation data, don't show the timeline chart.
- New insights use `has_data` field — components check `if (!insight || !insight.has_data) return null`.
- Dashboard components must check for meaningful data before rendering (e.g. `weekly_series.length > 0`, `subscriptions.length > 0`, `expensive_day != null`).
- KPI cards grid should adapt to however many cards have real data — no empty placeholder cards.
- Findings must describe what was actually found, not generic advice. If nothing was found, say so briefly (e.g. "No recurring charges found") and don't pad with filler.

### Plain language everywhere — no jargon
- **All user-facing text must be conversational and intuitive.** No "correlation coefficient", "r-value", "p-value", "statistically significant", "Pearson", "alignment", "insufficient variance", "lag_used".
- Write findings like you're explaining to a friend: "Busy weeks tend to push your spending up" not "Weak positive relationship using same_week_raw alignment (statistically significant)".
- The AI chat system prompt enforces this too — see `narrative_gen.py SYSTEM_PROMPT`.
- Evidence arrays should be human-readable: "Based on 12 weeks of spending data" not "Correlation coefficient: 0.42".

### User context collection
- The app provides a form on the YourData page for users to input personal financial context: income, savings goals, current savings, debt. This enriches insights like savings velocity and payday patterns.

### BYOK (Bring Your Own Key)
- Users can enter their own API key (Groq, OpenRouter, or OpenAI) directly in the chat panel via `ApiKeyConfig.tsx`.
- Keys are session-only — never persisted to disk or sent anywhere except the LLM provider.
- Server passes BYOK keys as env var overrides to Python subprocesses.

## Important Conventions

- After changing feature or insight logic, always regenerate cached insights and verify with `pytest`.
- Frozen caches in `outputs/` are what the UI reads — the app does not recompute insights live for demo personas.
- Environment requires one of `GROQ_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` in `.env` for narrative chat — OR users can BYOK in the chat UI.
- Groq keys start with `gsk_`. Uses OpenAI-compatible endpoint at `https://api.groq.com/openai/v1`.
- All persona data is 100% synthetic. Delete after March 31, 2026 per hackathon rules.
- On Windows, `NODE_ENV=x cmd` doesn't work. Start the two dev servers as separate processes (not combined with `&`): `npx tsx server/index.ts` (API on :5000) and `npx vite --host` (frontend on :5173).
