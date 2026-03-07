# LifeLedger Improvements — Partner Handoff

*Pull this file and pick items to work on. Check off as you complete them.*

---

## Hackathon Status (as of 2026-03-07)

**Deadline:** March 9, 2026 | **Track:** Data Portability Hackathon 2026, Track 3

### Done
- [x] Persona data, loaders, features, insight engine, Streamlit UI
- [x] Cached insights (`outputs/insights_p01.json`, `outputs/insights_p05.json`)
- [x] Welcome gate, KPI cards, timeline chart, spike evidence cards
- [x] Financial resilience layer (stability, volatility, runway, regret, decomposition)
- [x] Data Story + consent/privacy card
- [x] Demo script rehearsed

### Before Submission
- [ ] Run chat Q&A with live OpenAI key (5–10 benchmark prompts)
- [ ] Refresh `outputs/demo_backups/` via `python3 scripts/generate_demo_backups.py`
- [ ] Re-run `./scripts/demo_dry_run.sh`

---

## UI Improvements

*Main app: `src/ui/app.py`*

| # | Area | Location | Suggestion |
|---|------|----------|------------|
| 1 | Welcome gate | `_render_welcome_gate()` | Add subtle animation on CTA hover; consider mobile tap targets |
| 2 | KPI cards | `_render_kpi_row()`, `_render_metric_card()` | Add tooltips for "What this means" on hover; improve truncation for long theme lists |
| 3 | Stress vs spend chart | `_render_spike_chart()` | Add date range selector; improve spike marker visibility on dense data |
| 4 | Spike evidence cards | `_render_spike_details()` | Responsive grid for narrow screens (2-col → 1-col); loading skeleton |
| 5 | Resilience panel | `_render_resilience_panel()` | Add short help text for overlay toggles; improve decomposition bar labels |
| 6 | Chat shell | `_render_chat()` | Add suggested questions as quick chips; improve empty-state copy |
| 7 | Global styles | `_inject_global_style()` | Review `@media (max-width: 920px)` breakpoints; test on smaller viewports |
| 8 | Your Data tab | `main()` | Improve upload UX: drag-drop zones, file type validation feedback |

### Using Cursor Skills for UI Work

Create a project skill at `.cursor/skills/lifeledger-ui/SKILL.md` so the agent knows the UI stack:

- Stack: Streamlit, Plotly, custom CSS in `_inject_global_style()`
- CSS vars: `--bg`, `--card`, `--accent`, `--warn`, `--positive`
- Always use `escape()` for user content in HTML
- Test with both p01 and p05 personas

---

## Backend Logic Improvements

### High Priority

| # | File | Issue | Suggestion |
|---|------|-------|------------|
| 1 | `src/ui/app.py` | `compute_insights_from_uploads()` is a stub | Implement parsers for ChatGPT/Claude export, bank CSV, Google Calendar ICS so "Your Data" tab works |
| 2 | `src/insights/narrative_gen.py` | No retry/backoff | Add retries for API failures; truncate large insight payloads before sending to LLM |
| 3 | `src/insights/insight_engine.py` | Theme lexicon limited | Add more freelancer/ADHD phrases to `THEME_LEXICON`; improve invoice regex for varied email formats |

### Medium Priority

| # | File | Issue | Suggestion |
|---|------|-------|------------|
| 4 | `src/features/resilience_model.py` | Keyword-based inflow/fixed-load | Broaden `INFLOW_KEYWORDS` and `FIXED_LOAD_KEYWORDS`; add confidence scores for runway when balance is inferred |
| 5 | `src/insights/insight_engine.py` | Edge cases | Add validation for empty timelines, missing profile fields; fail gracefully with clear messages |
| 6 | `src/insights/narrative_gen.py` | Chat UX | Add optional streaming for chat responses |

### Optional (from judging checklist)

| # | Area | Suggestion |
|---|------|------------|
| 7 | BYOK support | Support hosted key (default), BYOK OpenAI, BYOK OpenRouter; keep keys session-only, never persisted |
| 8 | CPI/macro | Cache CPI data to reduce external FRED calls |

---

## Quick Reference

```bash
# Run app
streamlit run src/ui/app.py

# Regenerate insight cache (after feature/insight logic changes)
python3 -c "from src.insights.insight_engine import save_insights; save_insights('p01'); save_insights('p05')"

# Refresh demo backups
python3 scripts/generate_demo_backups.py

# Demo dry run checklist
./scripts/demo_dry_run.sh

# Compile check
python3 -m py_compile src/loaders/persona_loader.py src/features/stress_scorer.py src/features/spend_tagger.py src/features/correlation.py src/features/resilience_model.py src/insights/insight_engine.py src/insights/narrative_gen.py src/ui/app.py
```

---

## Context Files

- `context/PROJECT_CHECKLIST.md` — Master checklist, execution order
- `context/WORKLOG_STATUS.md` — Handoff tracker, owners, blockers
- `context/CORRECTION_ACTIONS_FOR_JUDGING.md` — Judge-readiness checklist
- `context/docs/resilience_metrics.md` — Resilience formulas and assumptions
