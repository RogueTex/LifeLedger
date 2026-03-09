# LifeLedger Collaboration Context & Checklist

Track: Data Portability Hackathon 2026 (Track 3)  
Deadline: March 9, 2026

## 1) Current Snapshot (As Of 2026-03-06)

- [x] Persona data for `p01` and `p05` is present in `data/raw/`
- [x] Loader, features, insight engine, narrative generator, web dashboard implemented
- [x] Validation notebook scaffold (`notebooks/eda.ipynb`) created with required cells
- [x] Cached insights generated: `outputs/insights_p01.json`, `outputs/insights_p05.json`
- [x] Schema and export docs moved to structured locations (`schemas/`, `context/docs/`)
- [x] Final contract alignment for judging (field-level schema + evidence richness)
- [x] Final demo polish + script rehearsal
- [x] UI/insight enhancement pass completed (trend chart, inference fallback, richer theme/rate signals)
- [x] Welcome transition screen + declutter pass completed (entry gate, compact KPI cards, full timeline chart, always-visible spike evidence cards)
- [x] Financial resilience metric layer completed (stability/volatility/runway/regret + decomposition + overlays)

## 2) Dataset Intake Checklist

Source Drive:
`https://drive.google.com/drive/folders/1TEWhdzff-FgkDNY-53IDXIWaPZQ7_5F3`

### Persona data required
- [x] `data/raw/persona_p01/persona_profile.json`
- [x] `data/raw/persona_p01/consent.json`
- [x] `data/raw/persona_p01/lifelog.jsonl`
- [x] `data/raw/persona_p01/conversations.jsonl`
- [x] `data/raw/persona_p01/emails.jsonl`
- [x] `data/raw/persona_p01/calendar.jsonl`
- [x] `data/raw/persona_p01/social_posts.jsonl`
- [x] `data/raw/persona_p01/transactions.jsonl`
- [x] `data/raw/persona_p01/files_index.jsonl`
- [x] `data/raw/persona_p01/README.md`
- [x] `data/raw/persona_p05/persona_profile.json`
- [x] `data/raw/persona_p05/consent.json`
- [x] `data/raw/persona_p05/lifelog.jsonl`
- [x] `data/raw/persona_p05/conversations.jsonl`
- [x] `data/raw/persona_p05/emails.jsonl`
- [x] `data/raw/persona_p05/calendar.jsonl`
- [x] `data/raw/persona_p05/social_posts.jsonl`
- [x] `data/raw/persona_p05/transactions.jsonl`
- [x] `data/raw/persona_p05/files_index.jsonl`
- [x] `data/raw/persona_p05/README.md`

### Root/support docs required
- [x] `QUICKSTART.md`
- [x] `schemas/DATASET_SCHEMA.md`
- [x] `context/docs/how_to_export_your_own_data.md`

## 3) Prompt Progress Matrix

| Prompt | Scope | Status | Notes |
|---|---|---|---|
| Prompt 1 | Project init + structure | ✅ Done | Directory and dependency baseline complete. |
| Prompt 2 | Loader + timeline | ✅ Done | Loader contract locked (`profile`, `consent`, normalized source keys, strict `year_week`). |
| Prompt 3 | Features | ✅ Done | Correlation reliability improved and spike evidence payload enriched. |
| Prompt 4 | Insight engine + narrative | ✅ Done | Insight schema locked + validated before save; inference fallbacks and expanded explainability added. |
| Prompt 5 | Web app | ✅ Done | UI + metrics + timeline chart + always-visible spike cards + chat integrated, plus welcome transition gate and resilience overlays. |
| Prompt 6 | Validation notebook | ✅ Done | Notebook file contains required 8-cell flow. |

## 4) High-Priority Gaps

- [x] Align loader keys and `year_week` formatting to final agreed contract (`YYYY-WW`)
- [x] Strengthen stress and spend feature variability so correlation is non-trivial
- [x] Expand spike-week evidence payload (`top_transactions`, `calendar_events`, `threshold_math`)
- [x] Normalize insight output schema to exact judging contract (`id/title/finding/evidence/dollar_impact`)
- [x] Improve metric completeness (`months_to_goal`) with robust fallback inference
- [x] Improve freelancer undercharging detection using invoice+calendar evidence
- [x] Add structural resilience metrics and decomposition with macro-aware adjustment
- [ ] Validate chat answer quality against 5-10 benchmark questions (live-key demo pass pending)

## 5) Execution Order (From Here)

1. Run benchmark chat QA (5-10 prompts) with live key and record grounded answers
2. Refresh `outputs/demo_backups/` via `python3 scripts/generate_demo_backups.py`
3. Re-run `./scripts/demo_dry_run.sh`

## 6) Validation Commands

```bash
python3 -m py_compile src/loaders/persona_loader.py src/features/stress_scorer.py src/features/spend_tagger.py src/features/correlation.py src/features/resilience_model.py src/insights/insight_engine.py src/insights/narrative_gen.py
```

```bash
cd web && npm run dev
```

```python
from src.insights.insight_engine import save_insights
save_insights("p01")
save_insights("p05")
```

## 7) Pre-Demo Checklist

- [x] `outputs/insights_p01.json` exists
- [x] `outputs/insights_p05.json` exists
- [x] Web app starts
- [x] Correlation for p01 is meaningful (target `r >= 0.3`) 
- [x] Spike-week explainers are populated with rich examples
- [x] Weekly trend chart renders with spike highlights
- [x] Spike evidence cards render top-3 weeks without expander interaction
- [x] Welcome transition gate routes correctly to Demo/Your Data
- [x] Months-to-goal card shows inferred value when direct fields are missing
- [x] Resilience panel renders baseline vs adjusted stability with overlay toggles
- [x] Decomposition chart renders without pie charts
- [ ] Chat Q&A tested with live OpenAI key and expected grounded behavior
- [x] Demo script rehearsed at 2 minutes end-to-end

## 8) Ownership Tracker

- [x] Owner A: Loader/schema contract alignment
- [x] Owner B: Feature tuning + spike evidence enrichment
- [x] Owner C: Insight output contract + narrative QA
- [x] Owner D: dashboard polish + chart/explainer UX
- [x] Owner E: Demo script + rehearsal + submission packaging

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
