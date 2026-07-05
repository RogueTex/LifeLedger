# LifeLedger Synthetic Sample Data

This directory contains privacy-safe synthetic fixtures for the raw ingestion path.

Use `data/sample/persona_pXX/` to inspect the raw JSON/JSONL persona schema.
Use `data/sample/uploads/` to exercise the user-upload flow with CSV, ICS, and ChatGPT-style JSON files.
Use `data/sample/EXPECTED_INSIGHTS.md` to see the deterministic outcomes these fixtures are expected to produce.

Regenerate these files with:

```bash
python scripts/generate_sample_data.py
```
