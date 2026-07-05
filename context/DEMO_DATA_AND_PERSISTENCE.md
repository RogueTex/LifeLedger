# Demo Data and Persistence

## Database

LifeLedger does not use a database in the current demo architecture. There are no migrations, ORM models, hosted database credentials, or local SQLite/Postgres files in the repository.

The demo server reads committed JSON insight payloads from `outputs/`, and the upload path computes insight JSON in memory for the current session.

## Shipped Sample Data

The repo does include frozen synthetic demo data:

- `outputs/insights_p01.json` — Jordan Lee
- `outputs/insights_p03.json` — Sasha Moreno
- `outputs/insights_p05.json` — Theo Nakamura
- `outputs/demo_backups/` — smaller backup payloads for demo panels

These files are enough to run the demo from a fresh clone.

## Raw Source Data

The repo now also includes committed synthetic raw fixtures:

- `data/sample/persona_p01/` — Jordan Lee raw JSON/JSONL files
- `data/sample/persona_p03/` — Sasha Moreno raw JSON/JSONL files
- `data/sample/persona_p05/` — Theo Nakamura raw JSON/JSONL files
- `data/sample/uploads/` — CSV, ICS, and ChatGPT-style JSON files for the upload flow

Regenerate them with:

```bash
python scripts/generate_sample_data.py
```

Private or personal source exports belong in `data/raw/`, which remains gitignored. You can also set `LIFELEDGER_PERSONA_DATA_DIR=/path/to/personas` to point the loader at an external persona directory.

The loader checks for persona folders in this order:

1. `LIFELEDGER_PERSONA_DATA_DIR/persona_pXX` when the environment variable is set
2. `data/raw/persona_pXX`
3. `data/sample/persona_pXX`

If raw folders are absent, the frozen `outputs/` files are still served normally by the web app.

## Production Direction

If this moved beyond demo mode, the natural persistence layer would be:

- object storage for uploaded raw files, gated by explicit consent;
- a relational database for analysis jobs, user-owned insight payloads, chat sessions, and audit metadata;
- a retention job that deletes raw uploads and derived artifacts according to user policy.

That split keeps the prototype privacy story simple while leaving a clear path to production storage.
