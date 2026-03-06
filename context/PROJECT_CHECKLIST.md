# LifeLedger Collaboration Context & Checklist

Track: Data Portability Hackathon 2026 (Track 3)  
Deadline: March 9, 2026

## 1) Current Snapshot (As Of 2026-03-06)

- [x] Persona data for `p01` and `p05` is present in `data/raw/`
- [x] Loader, features, insight engine, narrative generator, Streamlit UI implemented
- [x] Validation notebook scaffold (`notebooks/eda.ipynb`) created with required cells
- [x] Cached insights generated: `outputs/insights_p01.json`, `outputs/insights_p05.json`
- [x] Schema and export docs moved to structured locations (`schemas/`, `context/docs/`)
- [ ] Final contract alignment for judging (field-level schema + evidence richness)
- [ ] Final demo polish + script rehearsal

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
| Prompt 2 | Loader + timeline | 🟡 In Review | Works on real data; final schema contract should be re-checked. |
| Prompt 3 | Features | 🟡 In Review | Works end-to-end; spike/evidence enrichment can be improved. |
| Prompt 4 | Insight engine + narrative | 🟡 In Review | Pipeline works; output shape needs final rubric alignment. |
| Prompt 5 | Streamlit app | ✅ Done | UI + metrics + chart + expanders + chat integrated. |
| Prompt 6 | Validation notebook | ✅ Done | Notebook file contains required 8-cell flow. |

## 4) High-Priority Gaps

- [ ] Align loader keys and `year_week` formatting to final agreed contract (`YYYY-Www` vs current style)
- [ ] Strengthen stress and spend feature variability so correlation is non-trivial (current constant-series warning appears)
- [ ] Expand spike-week evidence payload (`top_transactions`, `calendar_events`) for richer demo explainability
- [ ] Normalize insight output schema to exact judging contract (`id/title/finding/evidence/dollar_impact`)
- [ ] Validate chat answer quality against 5-10 benchmark questions

## 5) Execution Order (From Here)

1. Contract alignment pass (Prompt 2/3/4 output shapes)
2. Run `notebooks/eda.ipynb` end-to-end and capture screenshots/notes
3. Regenerate `outputs/insights_p01.json` and `outputs/insights_p05.json`
4. UI polish + demo narrative pass
5. Final dry run (2-minute timed script)

## 6) Validation Commands

```bash
python3 -m py_compile src/loaders/persona_loader.py src/features/stress_scorer.py src/features/spend_tagger.py src/features/correlation.py src/insights/insight_engine.py src/insights/narrative_gen.py src/ui/app.py
```

```bash
streamlit run src/ui/app.py
```

```python
from src.insights.insight_engine import save_insights
save_insights("p01")
save_insights("p05")
```

## 7) Pre-Demo Checklist

- [x] `outputs/insights_p01.json` exists
- [x] `outputs/insights_p05.json` exists
- [x] Streamlit app starts
- [ ] Correlation for p01 is meaningful (target `r > 0.3`)
- [ ] Spike-week explainers are populated with rich examples
- [ ] Chat Q&A tested with live OpenAI key and expected grounded behavior
- [ ] Demo script rehearsed at 2 minutes end-to-end

## 8) Ownership Tracker

- [ ] Owner A: Loader/schema contract alignment
- [ ] Owner B: Feature tuning + spike evidence enrichment
- [ ] Owner C: Insight output contract + narrative QA
- [ ] Owner D: Streamlit polish + chart/explainer UX
- [ ] Owner E: Demo script + rehearsal + submission packaging

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
