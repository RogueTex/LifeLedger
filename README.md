# LifeLedger — Personal Finance Intelligence Engine

*"Connect your money to your life — not just your bank statement."*

Built for the **Data Portability Hackathon 2026**, **Track 3: Personal Data, Personal Value**. Submission deadline: **March 9, 2026**.

LifeLedger ingests exported personal data across transactions, calendar, emails, AI conversations, and lifelog streams to surface behavioral patterns invisible in any single source. The core thesis: financial behavior is driven by stress, emotional state, and calendar pressure, not just income and expenses.

## 📊 Status Table

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Repo setup & data files | ✅ Done |
| Phase 1 | Data loaders & timeline | ✅ Done |
| Phase 2 | Feature engineering | ✅ Done |
| Phase 3 | Insight engine | ✅ Done |
| Phase 4 | Streamlit UI | ✅ Done |
| Phase 5 | Demo polish & cache | ✅ Done |
| Phase 6 | Financial resilience metric layer | ✅ Done |

## 🗂️ Project Structure

```text
lifeledger/
├── context/
│   ├── PROJECT_CHECKLIST.md             # Master checklist + execution order + pre-demo gates
│   ├── WORKLOG_STATUS.md                # Collaborator handoff tracker (owners, status, blockers)
│   └── docs/
│       └── how_to_export_your_own_data.md
├── data/
│   ├── raw/
│   │   ├── persona_p01/                 # Jordan Lee synthetic exports
│   │   └── persona_p05/                 # Theo Nakamura synthetic exports
│   └── processed/
├── src/
│   ├── __init__.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── persona_loader.py            # Load JSON/JSONL persona data, normalize schemas, build timeline
│   ├── features/
│   │   ├── __init__.py
│   │   ├── stress_scorer.py             # Calendar-derived daily stress + smoothing
│   │   ├── spend_tagger.py              # Discretionary spend tagging + weekly totals
│   │   ├── correlation.py               # Stress/spend correlation + spike week detection
│   │   └── resilience_model.py          # Stability, volatility, runway, regret risk, macro-adjusted decomposition
│   ├── insights/
│   │   ├── __init__.py
│   │   ├── insight_engine.py            # End-to-end insight computation + cache writer
│   │   └── narrative_gen.py             # GPT-4o-mini narrative answer generation from cached insights
│   └── ui/
│       ├── __init__.py
│       └── app.py                       # Streamlit dashboard + spike explainers + grounded chat
├── notebooks/
│   └── eda.ipynb                        # Validation notebook (8 required cells)
├── outputs/
│   ├── insights_p01.json                # Frozen demo cache via save_insights("p01")
│   ├── insights_p05.json                # Frozen demo cache via save_insights("p05")
│   └── demo_backups/
│       ├── backup_p01.json              # Backup panel data for p01
│       └── backup_p05.json              # Backup panel data for p05
├── schemas/
│   └── DATASET_SCHEMA.md
├── requirements.txt
├── .env.example
├── .gitignore
├── QUICKSTART.md
├── scripts/
│   ├── demo_dry_run.sh                  # 2-minute timed demo runbook
│   └── generate_demo_backups.py         # Backup critical panel data per persona
└── README.md
```

## ⚡ Quickstart

1. Clone and install dependencies.

```bash
git clone https://github.com/RogueTex/LifeLedger.git
cd LifeLedger
python3 -m pip install -r requirements.txt
```

2. Configure environment.

```bash
cp .env.example .env
# Add OPENAI_API_KEY=... to .env
```

3. Download `persona_p01` and `persona_p05` from hackathon Google Drive into `data/raw/`.

Expected per persona (10 entries: 1 folder + 9 files):
- `persona_<id>/`
- `persona_profile.json`
- `consent.json`
- `lifelog.jsonl`
- `conversations.jsonl`
- `emails.jsonl`
- `calendar.jsonl`
- `social_posts.jsonl`
- `transactions.jsonl`
- `files_index.jsonl`

4. Run sanity check script.

```python
from pathlib import Path

for pid in ["p01", "p05"]:
    folder = Path(f"data/raw/persona_{pid}")
    expected = [
        "persona_profile.json", "consent.json", "lifelog.jsonl",
        "conversations.jsonl", "emails.jsonl", "calendar.jsonl",
        "social_posts.jsonl", "transactions.jsonl", "files_index.jsonl"
    ]
    missing = [f for f in expected if not (folder / f).exists()]
    if missing:
        print(f"❌ {pid} missing: {missing}")
    else:
        print(f"✅ {pid} — all files present")
```

5. Generate insight cache.

```python
from src.insights.insight_engine import save_insights

save_insights("p01")
save_insights("p05")
```

6. Run app.

```bash
streamlit run src/ui/app.py
```

## 🧠 How It Works

### Stress-Spend Correlation
Calendar events are transformed into daily stress scores, aggregated weekly, and evaluated against weekly discretionary spend across multiple valid alignments (same-week and prior-week variants). The engine selects the strongest valid signal, emits low-variance fallbacks when needed, and flags spike weeks with threshold math + transaction/event evidence. UI includes a full weekly timeline chart with spike highlights.

### Freelancer Business Brain (Theo / p05)
Emails plus calendar context are scanned for invoice/payment signals and implied hourly rate cues. If invoice messages contain dollar amounts but no explicit hours, the engine uses trailing calendar project hours as a fallback. If implied rate is below the **$65/hr Austin baseline**, the system raises an undercharging risk flag and estimates leakage.

### Cross-Source Insight Report
Conversation tags, lifelog patterns, and persona profile context are fused to produce anxiety theme recurrence, savings goal velocity (`months_to_goal`), and behavioral summaries. Theme extraction now combines explicit tags with a text lexicon (including freelancer-focused stress patterns).

### Financial Resilience Layer
`src/features/resilience_model.py` computes:
- `stability_score` and `stability_score_with_macro`
- `volatility_index`
- `liquidity_runway_days` (+ confidence band)
- `regret_risk_signal`
- decomposition percentages: behavioral, structural fixed load, income instability, macro pressure

Macro overlay uses CPI YoY (`CPIAUCSL`) with robust fallback order: provided series -> local cache (`data/processed/cpi_yoy_cache.csv`) -> deterministic FRED fetch -> deterministic synthetic fallback.

## 📐 Locked Contracts

### Loader Contract
- Top-level keys are fixed: `profile`, `consent`, `lifelog`, `conversations`, `emails`, `calendar`, `social_posts`, `transactions`, `files_index`.
- Normalized timeline columns include `ts`, `date`, `week`, `year_week`, `tags`, `refs`, `amount`, `text`, `source`.
- `year_week` is enforced as `YYYY-WW`.

### Insight Contract (`schema_version: v1_locked`)
Every insight row includes:
- `id`
- `title`
- `finding`
- `evidence` (list)
- `dollar_impact`

Stress/spend output also includes:
- `correlation_coefficient`, `p_value`, `insufficient_variance`, `lag_used`
- `weekly_series` for full-week trend rendering
- `spike_weeks` with `top_transactions`, `calendar_events`, and `threshold_math`

Savings-goal output includes:
- fallback estimation metadata (`estimation_mode`) when direct financial profile fields are missing

Resilience output IDs:
- `resilience_stability`
- `resilience_volatility_index`
- `resilience_liquidity_runway_forecast`
- `resilience_regret_risk_signal`
- `resilience_decomposition`

## 🧾 Data Sources Table

| File | Records | Used For |
|---|---:|---|
| `lifelog.jsonl` | 150 | emotional signals, behavioral arc |
| `conversations.jsonl` | varies | anxiety themes, decision patterns |
| `emails.jsonl` | 80 | invoice detection, deadline context |
| `calendar.jsonl` | 80 | stress scoring |
| `social_posts.jsonl` | 50 | spending trigger correlation (p05) |
| `transactions.jsonl` | 120 | core financial signal |
| `files_index.jsonl` | 40 | metadata |
| `persona_profile.json` | 1 | goals, income, debt baseline |
| `consent.json` | 1 | permitted use — read before touching data |

## 🎨 UX Flow

- App now opens on a transition gate: **Welcome to LifeLedger**.
- Centered animated logo with smooth entrance animation.
- Two entry routes:
  - `Start Now` opens the **Your Data** tab first.
  - `View Demo` opens the **Demo** tab first.
- Dashboard polish includes compact KPI cards, full-width timeline chart, always-visible spike evidence cards, and grounded chat.

## 🛠️ Tech Stack Table

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 runtime | pandas + json native |
| Data | pandas DataFrames | unified timeline across all sources |
| Features | Rule-based + statistical | deterministic, demo-safe |
| LLM | GPT-4o-mini via OpenAI | fast, cheap, narrative generation |
| UI | Streamlit | fastest path to polished interactive demo |
| Charts | Plotly | timeline chart, correlation scatter |
| Caching | JSON in `outputs/` | pre-generate before demo, avoid live compute |

## 👥 Personas

### Jordan Lee (p01)
Burnout + home savings goal. Primary demo story: stress-spend correlation, goal velocity, anxiety themes.

### Theo Nakamura (p05)
ADHD + freelance + undercharging. Secondary demo story: freelancer business brain, invoice tracking, implied rate alert.

## 🔒 Consent & Data Notes

- All data is 100% synthetic (`pii_level: "synthetic"` in records).
- Read `consent.json` before using any persona data.
- Data is processed locally.
- No raw data is sent to OpenAI; narrative chat uses structured insight JSON.
- Delete all synthetic data after **March 31, 2026** per hackathon rules.

## 🤝 Collaboration

- **Improvements backlog:** `IMPROVEMENTS.md` — UI and backend tasks for partners
- Master checklist: `context/PROJECT_CHECKLIST.md`
- Active handoff/status board: `context/WORKLOG_STATUS.md`
- Schema reference: `schemas/DATASET_SCHEMA.md`

## 🚀 What’s Next

- Run final live-key chat smoke test with benchmark prompts before judging
- Keep frozen caches and backup panel files in sync if feature logic changes
