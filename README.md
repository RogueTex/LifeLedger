# LifeLedger — Personal Finance Intelligence Engine

*"Your spending tells a story. Your calendar, conversations, and emotions tell the rest."*

Built for the **Data Portability Hackathon 2026**, **Track 3: Personal Data, Personal Value**.

---

## The Thesis

Your bank statement shows *what* you spent. LifeLedger shows *why*.

By fusing exported data across transactions, calendar events, AI conversation history, emails, and lifelog streams, LifeLedger surfaces behavioral patterns that are invisible in any single source. The core insight: **financial behavior is driven by stress, emotional state, and calendar pressure** — not just income and expenses.

This isn't a dashboard that reformats your bank CSV. It's a cross-source intelligence engine that detects non-obvious patterns like:

- **"Your discretionary spending spikes 40% in the week after high-stress calendar periods"** — by correlating Google Calendar meeting density with transaction amounts across multiple alignment windows
- **"You worry most about money in weeks where you also spend the most"** — by scanning ChatGPT/Claude conversation exports for anxiety keywords and overlaying them with weekly spend
- **"You're undercharging by $15/hr based on your invoice emails vs. calendar hours"** — by extracting dollar amounts from email text and inferring hours from trailing calendar project blocks
- **"62% of your spending happens within 3 days of payday"** — by detecting income deposits and measuring the post-payday spending concentration

None of these insights exist in any single data export. They only emerge when you connect the dots across sources — which is exactly what data portability makes possible.

---

## Why This Pushes Boundaries

### Cross-source fusion, not just display
Most personal finance tools read one data source and display it. LifeLedger merges **5+ data sources** into a unified behavioral timeline and runs correlation analysis across them. Calendar stress scores are compared against spending patterns. AI conversation sentiment is overlaid with financial behavior. Email invoice amounts are cross-referenced with calendar hours.

### Non-obvious, valuable insights
Every insight LifeLedger surfaces requires connecting at least two data sources:

| Insight | Sources Fused | What It Reveals |
|---|---|---|
| Stress-spend correlation | Calendar + Transactions | Busy weeks push spending up — with spike evidence |
| Worry timeline | AI conversations + Transactions | When anxiety peaks, so does discretionary spend |
| Invoice rate risk | Emails + Calendar | Freelancers can see if they're undercharging by inferring hourly rates |
| Post-payday surge | Transactions (income + spend) | Impulse spending concentrated right after income hits |
| Anxiety theme extraction | AI conversations + Lifelog | Recurring emotional patterns that drive financial decisions |
| Savings velocity | Transactions + User context | Goal-aware projections with months-to-target estimates |
| Stress category shift | Calendar + Transactions | Which spending categories change when life gets hectic |
| Spending velocity | Transactions (pay periods) | How fast you burn through budget each pay cycle |
| Recovery spending | Calendar + Transactions | "Treat yourself" purchases the week after high stress |
| Subscription creep | Transactions (recurring detection) | Passive drain from charges you forgot about |
| Day-of-week patterns | Transactions | Which day you consistently overspend (and by how much) |

### Bring Your Own Data — and your own AI key
Users can upload their own bank CSV (Chase, BofA, Amex, Mint), Google Calendar ICS, and ChatGPT/Claude conversation exports. Everything is processed locally. The AI chat supports **Bring Your Own Key** (Groq, OpenRouter, or OpenAI) — keys are session-only and never stored.

### Grounded AI chat
The narrative chat doesn't hallucinate. It receives only the precomputed insight JSON (never raw data) and answers questions strictly grounded in what the analysis actually found.

---

## Live Demo

Two synthetic personas demonstrate the engine's capabilities:

**Jordan Lee (p01)** — Burnout + home savings goal. Shows stress-spend correlation, spike week evidence with specific transactions and calendar events, worry timeline, subscription creep, and savings velocity tracking.

**Theo Nakamura (p05)** — ADHD + freelance. Shows invoice rate risk detection (undercharging at implied $50/hr vs. $65/hr Austin baseline), anxiety themes tied to client stress, and spending pattern analysis.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite | Fast SPA with type safety |
| Styling | Tailwind CSS + Framer Motion | Dark glass-panel aesthetic with smooth animations |
| Charts | Recharts | Composable timeline and bar charts |
| Routing | Wouter + TanStack Query | Lightweight client-side routing with data caching |
| API Server | Express 5 (TypeScript) | Bridges React frontend to Python compute layer |
| Compute | Python 3.12 + pandas | Feature engineering, correlation analysis, insight generation |
| LLM Chat | Groq / OpenRouter / OpenAI (BYOK) | Narrative answers grounded in insight JSON |
| Caching | JSON in `outputs/` | Pre-generated insights for demo reliability |

---

## Project Structure

```text
lifeledger/
├── web/                                    # React + Express web application
│   ├── client/src/
│   │   ├── pages/
│   │   │   ├── Welcome.tsx                 # Landing page with demo/upload routes
│   │   │   ├── Dashboard.tsx               # Demo persona analysis view
│   │   │   └── YourData.tsx                # User upload + analysis view
│   │   ├── components/dashboard/
│   │   │   ├── KPICards.tsx                 # Dynamic KPI grid (only renders real data)
│   │   │   ├── TimelineChart.tsx            # Stress x Spend correlation timeline
│   │   │   ├── WorryTimeline.tsx            # AI conversation worry x spending overlay
│   │   │   ├── SpikeEvidence.tsx            # Spike week drill-down with transactions + events
│   │   │   ├── SubscriptionPanel.tsx        # Recurring charge detection
│   │   │   ├── PostPaydaySurge.tsx          # Post-income spending concentration
│   │   │   ├── DayOfWeekChart.tsx           # Day-of-week spending patterns
│   │   │   ├── BehavioralInsights.tsx       # Theme extraction + rate risk + savings
│   │   │   ├── StrengthsWeaknesses.tsx      # Data-driven strengths/weaknesses summary
│   │   │   ├── DataUploadSection.tsx        # Multi-file drag-drop upload
│   │   │   ├── UserContextForm.tsx          # Income/savings/debt context form
│   │   │   ├── ApiKeyConfig.tsx             # BYOK API key input (session-only)
│   │   │   ├── GroundedChat.tsx             # AI chat for demo personas
│   │   │   └── GroundedChatUpload.tsx       # AI chat for user-uploaded data
│   │   └── lib/api.ts                      # API client + types
│   └── server/index.ts                     # Express API (5 endpoints)
├── src/
│   ├── loaders/
│   │   ├── persona_loader.py               # JSON/JSONL normalization → unified timeline
│   │   └── upload_parser.py                # Bank CSV, ICS, ChatGPT/Claude JSON/ZIP parsing
│   ├── features/
│   │   ├── stress_scorer.py                # Calendar → daily stress scores (meeting density + deadlines)
│   │   ├── spend_tagger.py                 # 9-category discretionary spend tagging
│   │   ├── correlation.py                  # Multi-alignment correlation + 3-tier spike detection
│   │   └── resilience_model.py             # Financial resilience metrics (stability, volatility, runway)
│   ├── insights/
│   │   ├── insight_engine.py               # End-to-end insight computation + schema validation
│   │   └── narrative_gen.py                # LLM narrative generation (Groq → OpenRouter → OpenAI)
├── scripts/
│   ├── process_upload.py                   # Bridge: stdin JSON → upload_parser → insights → stdout
│   ├── demo_dry_run.sh                     # 2-minute timed demo runbook
│   └── generate_demo_backups.py            # Backup panel data per persona
├── data/raw/persona_p{01,05}/              # Synthetic persona exports (10 files each)
├── outputs/
│   ├── insights_p01.json                   # Frozen demo cache — Jordan Lee
│   └── insights_p05.json                   # Frozen demo cache — Theo Nakamura
├── context/
│   └── docs/how_to_export_your_own_data.md # Guide for exporting your own data
└── schemas/DATASET_SCHEMA.md               # Full schema reference
```

---

## Quickstart

### Prerequisites
- Python 3.12+ with pip
- Node.js 20+

### 1. Install dependencies

```bash
git clone https://github.com/RogueTex/LifeLedger.git
cd LifeLedger
python -m pip install -r requirements.txt
cd web && npm install && cd ..
```

### 2. Configure environment (optional — for AI chat)

```bash
cp .env.example .env
# Add one of:
#   GROQ_API_KEY=gsk_...        (recommended — free, fast)
#   OPENROUTER_API_KEY=sk-or-...
#   OPENAI_API_KEY=sk-...
```

Or skip this — users can enter their own API key directly in the chat UI (BYOK).

### 3. Start the app (two terminals)

```bash
# Terminal 1: API server
cd web && npx tsx server/index.ts

# Terminal 2: Frontend
cd web && npx vite --host
```

Open **http://localhost:5173**. The API runs on `:5000`, and Vite proxies `/api` requests automatically.

### 4. Explore

- **View Demo** — Pre-analyzed synthetic personas (Jordan Lee, Theo Nakamura)
- **Analyze My Data** — Upload your own bank CSV, Google Calendar ICS, or ChatGPT/Claude exports
- **Ask AI** — Open the chat sidebar and ask questions about the insights (requires an API key via `.env` or BYOK)

---

## How It Works

### Stress-Spend Correlation Engine
Calendar events are scored for stress (meeting count, deadline keywords, packed schedules), smoothed over 7 days, and aggregated weekly. The engine tests **4 alignment strategies** (same-week smooth, prior-week smooth, same-week raw, prior-week raw) and selects the strongest valid signal. Spike weeks are detected with a **3-tier threshold** system that combines spending anomalies with stress levels, and each spike includes the top transactions and calendar events that explain it.

### Worry Timeline (Cross-Source Fusion)
AI conversation exports (ChatGPT, Claude) are scanned for 18 worry-related keywords across financial and emotional categories. Mentions are grouped by week and overlaid with discretionary spending to reveal when anxiety and spending move together — a pattern invisible in either source alone.

### Freelancer Business Brain
Email text is scanned for invoice/payment signals and dollar amounts. When explicit hours aren't stated, the engine infers them from trailing 28-day calendar project blocks. If the implied hourly rate falls below the **$65/hr market baseline**, it flags undercharging risk and estimates the monthly leakage.

### Upload Pipeline
Users upload files through a drag-and-drop interface. The system auto-classifies by extension, merges multiple files of the same type, and runs the full insight pipeline. An optional context form (income, savings goals, debt) enriches the analysis with goal-aware projections.

---

## Insight Schema (`v1_locked`)

Every insight includes: `id`, `title`, `finding`, `evidence[]`, `dollar_impact`, `what_this_means`, `recommended_next_actions[]`.

Up to 11 insight types are computed (all data-contingent — only generated when the data supports them):
- `stress_spend_correlation` — with `weekly_series[]`, `spike_weeks[]`, correlation stats
- `worry_timeline` — with `timeline[]`, `total_worry_mentions`, peak week
- `subscription_creep` — with `subscriptions[]`, `monthly_total`
- `expensive_day_of_week` — with `by_day{}`, `pct_above_average`
- `post_payday_surge` — with `surge_pct`, `post_payday_total`
- `months_to_goal` — with savings velocity and estimation mode
- `top_anxiety_themes` — with `top_themes[]` from conversation + lexicon
- `stress_category_shift` — which discretionary categories spike on high-stress weeks (calendar + transactions)
- `spending_velocity` — first-half vs second-half spend pacing within each pay period
- `recovery_spending` — spending increase the week after high-stress periods (decompression pattern)
- `invoice_rate_risk` — with `matches[]`, implied rates, leakage estimate (persona-specific)

---

## Data Portability in Action

LifeLedger exists because of data portability. Every insight requires data the user already has the right to export:

| Export | How to Get It | What LifeLedger Does With It |
|---|---|---|
| Bank transactions | Download CSV from Chase, BofA, Amex, Mint | Spending patterns, subscriptions, payday detection |
| Google Calendar | Settings → Import & Export → Export | Stress scoring, meeting density, deadline detection |
| ChatGPT history | Settings → Data Controls → Export | Worry timeline, anxiety themes, decision patterns |
| Claude history | claude.ai → Export conversations | Same as ChatGPT — merged into unified conversation stream |

See [`context/docs/how_to_export_your_own_data.md`](context/docs/how_to_export_your_own_data.md) for step-by-step export instructions.

---

## Privacy & Consent

- All demo data is **100% synthetic** (`pii_level: "synthetic"`)
- User-uploaded files are processed **locally in the browser session** — nothing is persisted
- The AI chat receives only **precomputed insight JSON**, never raw transaction data or files
- BYOK API keys are **session-only** and never written to disk
- Synthetic data will be deleted after **March 31, 2026** per hackathon rules

---

## Personas

### Jordan Lee (p01)
Burnout + home savings. Primary demo: stress-spend correlation with spike evidence, worry timeline showing anxiety-spending overlap, subscription creep detection, savings velocity to $50K goal.

### Theo Nakamura (p05)
ADHD + freelance. Secondary demo: invoice rate risk detection (undercharging $15/hr below market), ADHD/client-stress anxiety themes, spending pattern analysis without traditional income structure.
