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

The raw hackathon-style persona exports are not committed. `data/raw/` is intentionally gitignored because those folders are source material for regenerating caches, not runtime dependencies for the demo.

Regeneration paths such as `save_insights("p01")` expect `data/raw/persona_p01/` to exist locally. If those folders are absent, the frozen `outputs/` files are still served normally by the web app.

## Production Direction

If this moved beyond demo mode, the natural persistence layer would be:

- object storage for uploaded raw files, gated by explicit consent;
- a relational database for analysis jobs, user-owned insight payloads, chat sessions, and audit metadata;
- a retention job that deletes raw uploads and derived artifacts according to user policy.

That split keeps the prototype privacy story simple while leaving a clear path to production storage.
