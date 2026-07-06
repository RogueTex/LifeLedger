# Evaluation and Quality Story

LifeLedger's evaluation story is built around one principle: the model can help extract or explain, but every user-facing insight must be traceable to deterministic data contracts and regression tests.

## What Is Evaluated

| Layer | Evaluation Target | Current Check |
|---|---|---|
| Raw fixtures | Synthetic personas are complete and loadable | `TestSamplePersonaData.test_sample_personas_load_and_normalize` |
| Upload parser | CSV, ICS, and ChatGPT exports parse into usable rows | `TestSamplePersonaData.test_upload_fixtures_parse` |
| Typed extraction | Invoice emails become structured `invoice_payment` facts | `TestSamplePersonaData.test_structured_invoice_extraction_from_sample_emails` |
| Insight contract | Every insight follows the locked JSON schema | `_validate_insight_schema` and frozen output tests |
| Golden outcomes | Sample personas produce expected high-value insights | `test_sample_golden_insights_have_confidence_and_provenance` |
| Guardrails | Subscription logic avoids rent, grocery, and payroll false positives | `test_subscription_creep_ignores_rent_and_groceries` |
| Frontend contract | TypeScript, lint, and build catch UI/API drift | `npm --prefix web run check`, `lint`, and `build` |

## Golden Fixture Strategy

The committed `data/sample/` fixtures are synthetic but shaped like real exports:

- `persona_p01`: burnout, home savings, stress-spend correlation, subscriptions.
- `persona_p03`: high-stress professional with the clearest correlation and payday surge.
- `persona_p05`: ADHD/freelance workflow with invoice rate risk and structured email facts.
- `data/sample/uploads/`: standalone CSV, ICS, and ChatGPT files for the live upload path.

`data/sample/EXPECTED_INSIGHTS.md` documents what the engine should find. The Python tests then assert the most important outcomes so changes to parsers, extraction, thresholds, or schema cannot silently weaken the demo.

## Confidence and Provenance Contract

Every computed insight is expected to carry:

- `confidence.level`, `confidence.score`, and `confidence.rationale`
- `provenance.source_types`
- `provenance.method`
- `provenance.source_record_counts`
- `provenance.evidence_refs` when source-level IDs are available

The React dashboard exposes this in the Insight Audit Trail panel. That makes the evaluation story visible in the product: a reviewer can see how a claim is scored, which sources contributed, which deterministic method ran, and which source IDs back the result.

## AI Quality Boundary

The current system does not ask an LLM to make financial conclusions directly.

1. Parsers normalize source files.
2. Extractors create typed facts with source IDs and confidence.
3. Deterministic features compute correlations, thresholds, and dollar impact.
4. The insight engine emits locked JSON with evidence.
5. The grounded chat answers only from that JSON.

This keeps the system defensible under engineering review: if an answer is wrong, there is a clear place to inspect the parser, extractor, feature, or prompt boundary.

## Current Verification Commands

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests scripts
npm --prefix web run check
npm --prefix web run lint
npm --prefix web run build
```

## Production Evaluation Additions

A production version should add:

- parser versioning and replay reports by file hash
- labeled extraction sets for invoice, worry, subscription, and calendar stress cases
- precision/recall tracking for typed fact extraction
- canary personas for model/provider changes
- drift alerts when insight counts, confidence distributions, or dollar impacts change unexpectedly
- prompt and model trace IDs attached to extraction facts
- PII-safe logs with source IDs, not raw personal text
