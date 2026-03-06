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
| Phase 4 | Streamlit UI | 🔲 Next |
| Phase 5 | Demo polish & cache | 🔲 Next |

## 🗂️ Project Structure

```text
lifeledger/
├── data/
│   ├── raw/
│   │   ├── persona_p01/                 # Jordan Lee synthetic exports
│   │   └── persona_p05/                 # Theo Nakamura synthetic exports
│   └── processed/                       # Optional normalized/intermediate artifacts
├── src/
│   ├── __init__.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── persona_loader.py            # Load JSON/JSONL persona data, normalize schemas, build timeline
│   ├── features/
│   │   ├── __init__.py
│   │   ├── stress_scorer.py             # Calendar-derived daily stress + smoothing
│   │   ├── spend_tagger.py              # Discretionary spend tagging + weekly totals
│   │   └── correlation.py               # Stress/spend correlation + spike week detection
│   ├── insights/
│   │   ├── __init__.py
│   │   ├── insight_engine.py            # End-to-end insight computation + cache writer
│   │   └── narrative_gen.py             # GPT-4o-mini narrative answer generation from cached insights
│   └── ui/
│       ├── __init__.py
│       └── app.py                       # Streamlit entrypoint (next phase)
├── notebooks/
│   └── eda.ipynb                        # Exploratory analysis notebook
├── outputs/
│   ├── insights_p01.json                # Generated cache via save_insights("p01")
│   └── insights_p05.json                # Generated cache via save_insights("p05")
├── schemas/                             # Optional schema docs/contracts
├── requirements.txt
├── .env.example
├── .gitignore
├── QUICKSTART.md
└── README.md
```

## ⚡ Quickstart

1. Clone and install dependencies.

```bash
git clone https://github.com/RogueTex/LifeLedger.git
cd LifeLedger
pip install -r requirements.txt
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

ROOT = Path("data/raw")
PERSONAS = ["p01", "p05"]
REQUIRED_FILES = [
    "persona_profile.json",
    "consent.json",
    "lifelog.jsonl",
    "conversations.jsonl",
    "emails.jsonl",
    "calendar.jsonl",
    "social_posts.jsonl",
    "transactions.jsonl",
    "files_index.jsonl",
]

for pid in PERSONAS:
    pdir = ROOT / f"persona_{pid}"
    ok = pdir.exists()
    missing = []
    for name in REQUIRED_FILES:
        if not (pdir / name).exists():
            ok = False
            missing.append(name)
    if ok:
        print(f"✅ persona_{pid}: all files present")
    else:
        print(f"❌ persona_{pid}: missing -> {', '.join(missing) if missing else 'folder'}")
```

5. Generate insight cache.

```python
from src.insights.insight_engine import save_insights

save_insights("p01")
save_insights("p05")
```

6. Run app (coming next).

```bash
streamlit run src/ui/app.py
```

## 🧠 How It Works

### Stress-Spend Correlation
Calendar events are transformed into daily stress scores, then smoothed and aggregated weekly. Weekly stress averages are Pearson-correlated against weekly discretionary spend. The engine also flags top 3 spend spike weeks with explicit threshold and prior-week stress evidence.

### Freelancer Business Brain (Theo / p05)
Emails plus calendar context are scanned for invoice/payment signals and implied hourly rate cues. If implied rate is below the **$65/hr Austin baseline**, the system raises an undercharging risk flag with extracted evidence.

### Cross-Source Insight Report
Conversation tags, lifelog patterns, and persona profile context are fused to produce anxiety theme recurrence, savings goal velocity (`months_to_goal`), and a compact behavioral arc that explains why money outcomes shift.

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

## 🛠️ Tech Stack Table

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | pandas + json native |
| Data | pandas DataFrames | unified timeline across all sources |
| Features | Rule-based + statistical | deterministic, demo-safe |
| LLM | GPT-4o-mini via OpenAI | fast, cheap, narrative generation |
| UI | Streamlit | fastest path to polished interactive demo |
| Charts | Plotly | timeline chart, correlation scatter |
| Caching | JSON in `outputs/` | pre-generate before demo, never call live |

## 👥 Personas

### Jordan Lee (p01)
Burnout + home savings goal. Primary demo story: stress-spend correlation, slowing goal velocity, and anxiety theme recurrence.

### Theo Nakamura (p05)
ADHD + freelance + undercharging. Secondary demo story: freelancer business brain, invoice tracking, and implied hourly rate alert.

## 🔒 Consent & Data Notes

- All data is 100% synthetic (`pii_level: "synthetic"` in every record).
- Read `consent.json` before using any persona data.
- Data is processed locally and never uploaded to third-party services.
- No raw data is sent to OpenAI; only structured insight JSON is used for narrative generation.
- Delete all synthetic data after **March 31, 2026** per hackathon rules.

## 🚀 What’s Next

- Build Streamlit UI (Prompt 5)
- Pre-generate and cache all insight JSONs before demo
- Practice 2-minute demo script: Jordan → spike weeks → Theo → chat Q&A
- Write data story section for Human-Centric Design bonus award
