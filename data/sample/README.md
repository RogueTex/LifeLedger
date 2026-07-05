# LifeLedger Synthetic Sample Data

This directory contains privacy-safe synthetic fixtures for the raw ingestion path.

Use `data/sample/persona_pXX/` to inspect the raw JSON/JSONL persona schema.
Use `data/sample/uploads/` to exercise the user-upload flow with CSV, ICS, and ChatGPT-style JSON files.

Regenerate these files with:

```bash
python scripts/generate_sample_data.py
```
