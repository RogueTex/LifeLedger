"""Generate committed synthetic sample data for LifeLedger.

The output is privacy-safe fixture data under data/sample/. It mirrors the
hackathon persona schema closely enough to exercise the full ingestion path
without committing private data or relying on hidden data/raw folders.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
UPLOAD_DIR = SAMPLE_DIR / "uploads"
TZ_SUFFIX = "-05:00"


@dataclass(frozen=True)
class PersonaSpec:
    persona_id: str
    name: str
    age: int
    role: str
    city: str
    goal: str
    stress_story: str
    savings_goal: float
    current_savings: float
    avg_net_monthly_savings: float
    paycheck_amount: float
    high_stress_weeks: tuple[int, ...]
    subscription_names: tuple[str, ...]
    freelance: bool = False


PERSONAS = [
    PersonaSpec(
        persona_id="p01",
        name="Jordan Lee",
        age=32,
        role="Senior Product Manager",
        city="Austin, TX",
        goal="Save $50000 for a first home while keeping burnout under control.",
        stress_story="Promotion cycle creates deadline pressure and convenience spending.",
        savings_goal=50000,
        current_savings=18500,
        avg_net_monthly_savings=1250,
        paycheck_amount=3900,
        high_stress_weeks=(3, 4, 8, 11),
        subscription_names=("Netflix", "Spotify", "Figma Professional"),
    ),
    PersonaSpec(
        persona_id="p03",
        name="Sasha Moreno",
        age=37,
        role="Operations Strategy Lead",
        city="Austin, TX",
        goal="Build a $12000 emergency buffer while reducing post-payday spending spikes.",
        stress_story="Exec reviews and staffing escalations make money worries more frequent.",
        savings_goal=12000,
        current_savings=4200,
        avg_net_monthly_savings=700,
        paycheck_amount=3250,
        high_stress_weeks=(2, 5, 6, 10, 13),
        subscription_names=("CorePower Yoga", "Dovetail", "LinkedIn Premium"),
    ),
    PersonaSpec(
        persona_id="p05",
        name="Theo Nakamura",
        age=23,
        role="Freelance Designer",
        city="Austin, TX",
        goal="Pay down $8000 of debt and raise client rates to sustainable levels.",
        stress_story="Client deadlines, scope creep, and underpriced invoices create cash pressure.",
        savings_goal=8000,
        current_savings=900,
        avg_net_monthly_savings=350,
        paycheck_amount=1800,
        high_stress_weeks=(1, 4, 7, 9, 12),
        subscription_names=("Adobe Creative Cloud", "Webflow", "Notion AI"),
        freelance=True,
    ),
]


def iso(day: date, hour: int = 9, minute: int = 0) -> str:
    return f"{day.isoformat()}T{hour:02d}:{minute:02d}:00{TZ_SUFFIX}"


def json_dump(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def jsonl_dump(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(text + "\n", encoding="utf-8")


def base_record(record_id: str, ts: str, source: str, record_type: str, text: str, tags: list[str]) -> dict[str, Any]:
    return {
        "id": record_id,
        "ts": ts,
        "source": source,
        "type": record_type,
        "text": text,
        "tags": tags,
        "refs": [],
        "pii_level": "synthetic",
    }


def profile(spec: PersonaSpec) -> dict[str, Any]:
    return {
        "persona_id": spec.persona_id,
        "name": spec.name,
        "age": spec.age,
        "location": spec.city,
        "role": spec.role,
        "goals": [spec.goal],
        "pain_points": [spec.stress_story],
        "savings_goal": spec.savings_goal,
        "current_savings": spec.current_savings,
        "avg_net_monthly_savings": spec.avg_net_monthly_savings,
        "income_approx": f"${round(spec.paycheck_amount * 26):,.0f}/year",
        "notes": "Synthetic fixture persona for LifeLedger ingestion and inference demos.",
    }


def consent() -> dict[str, Any]:
    return {
        "dataset_type": "synthetic",
        "allowed_uses": ["local_demo", "testing", "model_prompting", "portfolio_review"],
        "prohibited_uses": ["attempt_reidentification", "training_production_models"],
        "retention": "no_real_personal_data",
        "notes": "Generated synthetic fixture data. No real individuals are represented.",
    }


def calendar_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 1
    for week in range(14):
        monday = start + timedelta(weeks=week)
        stress = 5 if week in spec.high_stress_weeks else 2 + (week % 2)
        titles = [
            "Weekly planning sync",
            "Budget review",
            "Customer follow-up",
            "1:1 coaching",
            "Launch deadline review",
            "Executive presentation prep",
            "OKR risk review",
        ]
        if spec.freelance:
            titles = [
                "Client design block 3h",
                "Portfolio review",
                "Invoice follow-up",
                "Brand presentation deadline",
                "Client revisions 4h",
                "Scope review",
                "Proposal work 2h",
            ]
        for event_num in range(stress):
            day = monday + timedelta(days=1 + (event_num % 4))
            hour = 9 + event_num
            title = titles[event_num % len(titles)]
            record = base_record(
                f"cal_{idx:04d}",
                iso(day, hour),
                "calendar",
                "event",
                f"{title} - {'high pressure week' if week in spec.high_stress_weeks else 'normal cadence'}",
                ["work", "deadline"] if any(word in title.lower() for word in ("deadline", "review", "presentation")) else ["work"],
            )
            record["title"] = title
            record["start"] = iso(day, hour)
            record["end"] = iso(day, hour + 1)
            rows.append(record)
            idx += 1
    return rows


def transaction_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 1
    for week in range(14):
        monday = start + timedelta(weeks=week)
        if week % 2 == 0:
            rows.append(txn(idx, monday, "Payroll direct deposit", spec.paycheck_amount, ["income"]))
            idx += 1
        if week in (0, 4, 8, 12):
            rows.append(txn(idx, monday + timedelta(days=1), "Avenue Place Rent", -1650, ["housing"]))
            idx += 1
        rows.append(txn(idx, monday + timedelta(days=2), "H-E-B Groceries", -88 - (week % 4) * 7, ["groceries"]))
        idx += 1
        rows.append(txn(idx, monday + timedelta(days=3), "Starbucks Coffee", -6.25, ["coffee"]))
        idx += 1
        rows.append(txn(idx, monday + timedelta(days=4), "Local Restaurant Dinner", -34.80, ["dining"]))
        idx += 1
        for sub_num, sub_name in enumerate(spec.subscription_names):
            if week in (0, 4, 8, 12):
                rows.append(txn(idx, monday + timedelta(days=sub_num + 2), f"{sub_name} monthly subscription", -18.99 - sub_num * 7, ["subscriptions"]))
                idx += 1
        if week in spec.high_stress_weeks:
            spike_items = [
                ("Uber Eats deadline dinner", -43.50, ["food_delivery", "stress"]),
                ("Amazon one-click work supplies", -119.40, ["shopping", "impulse"]),
                ("Lyft after late meeting", -27.80, ["rideshare"]),
            ]
            for offset, (merchant, amount, tags) in enumerate(spike_items):
                rows.append(txn(idx, monday + timedelta(days=offset + 2), merchant, amount, tags))
                idx += 1
        if spec.freelance and week in (1, 5, 9, 13):
            rows.append(txn(idx, monday + timedelta(days=4), "Client invoice payment", 750, ["income", "freelance"]))
            idx += 1
    return rows


def txn(idx: int, day: date, merchant: str, amount: float, tags: list[str]) -> dict[str, Any]:
    record = base_record(f"t_{idx:04d}", iso(day, 12), "bank", "transaction", merchant, tags)
    record["merchant"] = merchant
    record["amount"] = round(amount, 2)
    return record


def conversation_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 1
    for week in range(14):
        monday = start + timedelta(weeks=week)
        high = week in spec.high_stress_weeks
        text = (
            f"I am anxious about money this week. {spec.stress_story} "
            "I keep spending on convenience when the calendar gets packed."
            if high
            else f"Weekly check-in: I want to stay focused on my goal. {spec.goal}"
        )
        rows.append(base_record(
            f"c_{idx:04d}",
            iso(monday + timedelta(days=3), 20),
            "ai_chat",
            "conversation",
            text,
            ["anxiety", "money", "stress"] if high else ["goals", "planning"],
        ))
        idx += 1
    return rows


def email_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 1
    for week in range(14):
        monday = start + timedelta(weeks=week)
        if spec.freelance and week in (1, 5, 9, 13):
            text = "Invoice for client brand package: $750 for 15 hours. Payment due Friday."
            tags = ["invoice", "client", "undercharging"]
        elif week in spec.high_stress_weeks:
            text = f"Reminder: deadline review for {spec.name}. Please send the final deck before Thursday."
            tags = ["deadline", "work"]
        else:
            text = "Weekly status update and next steps."
            tags = ["work"]
        record = base_record(f"e_{idx:04d}", iso(monday + timedelta(days=2), 10), "email", "inbox", text, tags)
        record["subject"] = "Invoice follow-up" if spec.freelance and week in (1, 5, 9, 13) else "Weekly update"
        rows.append(record)
        idx += 1
    return rows


def lifelog_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for week in range(14):
        monday = start + timedelta(weeks=week)
        high = week in spec.high_stress_weeks
        text = (
            f"Felt the pressure today. {spec.stress_story} Need to watch convenience spending."
            if high
            else f"Kept a steady week and made progress toward: {spec.goal}"
        )
        rows.append(base_record(
            f"ll_{week + 1:04d}",
            iso(monday + timedelta(days=5), 8),
            "lifelog",
            "reflection",
            text,
            ["stress", "money"] if high else ["progress", "goals"],
        ))
    return rows


def social_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(1, 7):
        day = start + timedelta(days=idx * 12)
        rows.append(base_record(
            f"s_{idx:04d}",
            iso(day, 18),
            "social",
            "post",
            f"Shared a synthetic update about work, goals, and staying intentional with money as {spec.role}.",
            ["work", "goals"],
        ))
    return rows


def file_rows(spec: PersonaSpec, start: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    names = ["budget_review.xlsx", "goal_plan.md", "invoice_tracker.csv", "calendar_export.ics", "notes.txt"]
    for idx, name in enumerate(names, start=1):
        record = base_record(
            f"f_{idx:04d}",
            iso(start + timedelta(days=idx * 10), 15),
            "files",
            "file_metadata",
            f"{name} - synthetic file metadata for {spec.name}",
            ["finance"] if "budget" in name or "invoice" in name else ["planning"],
        )
        record["filename"] = name
        record["mime_type"] = "text/plain" if name.endswith(".txt") else "application/octet-stream"
        rows.append(record)
    return rows


def write_persona(spec: PersonaSpec) -> dict[str, list[dict[str, Any]]]:
    persona_dir = SAMPLE_DIR / f"persona_{spec.persona_id}"
    start = date(2026, 1, 5)
    rows_by_file = {
        "lifelog": lifelog_rows(spec, start),
        "conversations": conversation_rows(spec, start),
        "emails": email_rows(spec, start),
        "calendar": calendar_rows(spec, start),
        "social_posts": social_rows(spec, start),
        "transactions": transaction_rows(spec, start),
        "files_index": file_rows(spec, start),
    }

    json_dump(persona_dir / "persona_profile.json", profile(spec))
    json_dump(persona_dir / "consent.json", consent())
    for name, rows in rows_by_file.items():
        jsonl_dump(persona_dir / f"{name}.jsonl", rows)
    (persona_dir / "README.md").write_text(
        f"# {spec.name} ({spec.persona_id})\n\n"
        f"Synthetic fixture persona for LifeLedger.\n\n"
        f"- Role: {spec.role}\n"
        f"- Goal: {spec.goal}\n"
        f"- Embedded pattern: {spec.stress_story}\n",
        encoding="utf-8",
    )
    return rows_by_file


def write_upload_fixtures(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    txn_rows = rows_by_file["transactions"][:35]
    with (UPLOAD_DIR / "sample_transactions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Description", "Amount", "Category"])
        writer.writeheader()
        for row in txn_rows:
            day = row["ts"][:10]
            writer.writerow({
                "Date": day,
                "Description": row["text"],
                "Amount": f"{float(row['amount']):.2f}",
                "Category": row["tags"][0] if row["tags"] else "",
            })

    ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//LifeLedger//Synthetic Sample//EN"]
    for row in rows_by_file["calendar"][:18]:
        ts = datetime.fromisoformat(row["ts"]).astimezone(timezone.utc)
        end = ts + timedelta(hours=1)
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{row['id']}@lifeledger.local",
            f"DTSTART:{ts.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{row.get('title', row['text'])}",
            f"DESCRIPTION:{row['text']}",
            "END:VEVENT",
        ])
    ics_lines.append("END:VCALENDAR")
    (UPLOAD_DIR / "sample_calendar.ics").write_text("\n".join(ics_lines) + "\n", encoding="utf-8")

    conversations = []
    for idx, row in enumerate(rows_by_file["conversations"][:8], start=1):
        ts = int(datetime.fromisoformat(row["ts"]).timestamp())
        conversations.append({
            "title": f"Money check-in {idx}",
            "create_time": ts,
            "mapping": {
                f"u{idx}": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": [row["text"]]},
                        "create_time": ts,
                    },
                },
            },
        })
    (UPLOAD_DIR / "sample_chatgpt_export.json").write_text(
        json.dumps(conversations, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_sample_readme() -> None:
    (SAMPLE_DIR / "README.md").write_text(
        "# LifeLedger Synthetic Sample Data\n\n"
        "This directory contains privacy-safe synthetic fixtures for the raw ingestion path.\n\n"
        "Use `data/sample/persona_pXX/` to inspect the raw JSON/JSONL persona schema.\n"
        "Use `data/sample/uploads/` to exercise the user-upload flow with CSV, ICS, and ChatGPT-style JSON files.\n\n"
        "Regenerate these files with:\n\n"
        "```bash\n"
        "python scripts/generate_sample_data.py\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> None:
    first_persona_rows: dict[str, list[dict[str, Any]]] | None = None
    for spec in PERSONAS:
        rows = write_persona(spec)
        if spec.persona_id == "p01":
            first_persona_rows = rows
    if first_persona_rows is None:
        raise RuntimeError("Expected p01 rows for upload fixtures")
    write_upload_fixtures(first_persona_rows)
    write_sample_readme()


if __name__ == "__main__":
    main()
