# LifeLedger Collaboration Context & Checklist

Track: Data Portability Hackathon 2026 (Track 3)  
Deadline: March 9, 2026

## 1) Dataset Intake Checklist

Source Drive:
`https://drive.google.com/drive/folders/1TEWhdzff-FgkDNY-53IDXIWaPZQ7_5F3`

### Persona data required
- [ ] `data/raw/persona_p01/persona_profile.json`
- [ ] `data/raw/persona_p01/consent.json`
- [ ] `data/raw/persona_p01/lifelog.jsonl`
- [ ] `data/raw/persona_p01/conversations.jsonl`
- [ ] `data/raw/persona_p01/emails.jsonl`
- [ ] `data/raw/persona_p01/calendar.jsonl`
- [ ] `data/raw/persona_p01/social_posts.jsonl`
- [ ] `data/raw/persona_p01/transactions.jsonl`
- [ ] `data/raw/persona_p01/files_index.jsonl`
- [ ] `data/raw/persona_p01/README.md`
- [ ] `data/raw/persona_p05/persona_profile.json`
- [ ] `data/raw/persona_p05/consent.json`
- [ ] `data/raw/persona_p05/lifelog.jsonl`
- [ ] `data/raw/persona_p05/conversations.jsonl`
- [ ] `data/raw/persona_p05/emails.jsonl`
- [ ] `data/raw/persona_p05/calendar.jsonl`
- [ ] `data/raw/persona_p05/social_posts.jsonl`
- [ ] `data/raw/persona_p05/transactions.jsonl`
- [ ] `data/raw/persona_p05/files_index.jsonl`
- [ ] `data/raw/persona_p05/README.md`

### Root docs required
- [ ] `QUICKSTART.md` (Drive root copy)
- [ ] `DATASET_SCHEMA.md`
- [ ] `how_to_export_your_own_data.md`

Current repo state snapshot:
- `data/raw/` folders exist but are empty.
- `outputs/` has no cached insights yet.

## 2) Prompt Progress Matrix

| Prompt | Scope | Status | Notes |
|---|---|---|---|
| Prompt 1 | Project init + structure | 🟡 Partial | Structure and requirements created; `.env.example` and `.gitignore` need verification/update to exact spec. |
| Prompt 2 | Loader + timeline | 🟡 Partial | Implemented, but schema key names/`year_week` format and strict normalization should be verified against instruction text. |
| Prompt 3 | Features | 🟡 Partial | Implemented core logic, but current formulas and evidence outputs differ from detailed Prompt 3 spec. |
| Prompt 4 | Insight engine + narrative | 🟡 Partial | Pipeline exists; output schema and some calculations differ from requested contract. |
| Prompt 5 | Streamlit app | 🔴 Not started | `src/ui/app.py` is currently empty. |
| Prompt 6 | Validation notebook | 🔴 Not started | `notebooks/eda.ipynb` is currently empty placeholder. |

## 3) Must-Fix Gaps Before Demo

### Infra and repo hygiene
- [ ] Update `.env.example` to include `OPENAI_API_KEY=sk-your-key-here`.
- [ ] Update `.gitignore` to include `.env`, `data/raw/`, `__pycache__/`, `*.pyc`, `.DS_Store`.
- [ ] Remove/ignore any generated `__pycache__` artifacts from git tracking if present.

### Prompt 2 alignment (loader)
- [ ] Ensure return keys use exact contract (`profile`, `consent`, source names).
- [ ] Ensure `year_week` matches required format (`YYYY-Www` if using prompt spec literally).
- [ ] Ensure `amount` is `None` for all non-transaction rows.
- [ ] Re-run timeline merge checks with real persona data.

### Prompt 3 alignment (features)
- [ ] `stress_scorer`: meeting count must only include events tagged `work` or `meeting`.
- [ ] `stress_scorer`: apply free block rule exactly (`>4 events => free_block_flag=0 else 1`).
- [ ] `spend_tagger`: add explicit non-discretionary tag logic from spec.
- [ ] `correlation`: attach top 3 transactions and up to 3 calendar events per spike week.

### Prompt 4 alignment (insights)
- [ ] Match exact output schema (`id`, `title`, `finding`, `evidence`, `dollar_impact`, etc.).
- [ ] Compute `avg_net_monthly_savings` from transactions monthly income-expense deltas.
- [ ] Keep p05 undercharging logic and ensure insight id is `undercharging_alert`.
- [ ] `save_insights` should print confirmation path.
- [ ] `narrative_gen` should use the exact system prompt + `max_tokens=300`.

### Prompt 5/6 delivery
- [ ] Build full Streamlit UI in `src/ui/app.py`.
- [ ] Build full validation notebook in `notebooks/eda.ipynb` with 8 required cells.

## 4) Execution Order (Team)

1. Prompt 2/3/4 spec alignment pass (code contract correctness)
2. Drop persona files into `data/raw/`
3. Run sanity check script (below)
4. Build and run validation notebook (Prompt 6)
5. Generate caches: `outputs/insights_p01.json`, `outputs/insights_p05.json`
6. Build Streamlit UI last (Prompt 5)
7. Rehearse 2-minute demo flow

## 5) Sanity Check Script (Run First After Data Drop)

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

## 6) Pre-Demo Checklist

- [ ] `outputs/insights_p01.json` exists and has spike weeks
- [ ] `outputs/insights_p05.json` exists and has undercharging alert
- [ ] Streamlit app loads for both personas without errors
- [ ] Chat Q&A works with valid OpenAI key
- [ ] Correlation for p01 is meaningful (target `r > 0.3`)
- [ ] No live heavy computation during judging (use cached outputs)

## 7) Git Collaboration Workflow

- [ ] Create branch per task: `feat/prompt5-ui`, `feat/prompt6-notebook`, `fix/loader-contract`
- [ ] Keep PRs scoped to one prompt or one gap set
- [ ] Before push: run local sanity checks and attach outputs/screenshots
- [ ] Merge order: data contract fixes -> insight cache -> UI polish

## 8) Ownership Tracker

- [ ] Owner A: Data ingestion + loader contract
- [ ] Owner B: Feature engineering alignment
- [ ] Owner C: Insight schema + narrative generator
- [ ] Owner D: Streamlit UI + demo script prep
- [ ] Owner E: Validation notebook + QA

## 9) Key Schema Reference

| Prefix | File |
|---|---|
| `ll_` | lifelog |
| `c_` | conversations |
| `e_` | emails |
| `cal_` | calendar |
| `s_` | social_posts |
| `t_` | transactions |
| `f_` | files_index |

```json
{
  "id": "ll_0001",
  "ts": "2024-04-13T08:12:00-05:00",
  "source": "lifelog",
  "type": "reflection",
  "text": "Woke up tired again. Mind already on the roadmap review.",
  "tags": ["sleep", "work", "anxiety"],
  "refs": ["cal_0014"],
  "pii_level": "synthetic"
}
```

All data is synthetic. Delete after March 31, 2026 per hackathon rules.
