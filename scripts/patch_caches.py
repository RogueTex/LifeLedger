"""Patch existing insight caches: remove resilience insights, add new actionable insights."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REMOVE_IDS = {
    "resilience_stability",
    "resilience_volatility_index",
    "resilience_liquidity_runway_forecast",
    "resilience_regret_risk_signal",
    "resilience_decomposition",
}

P01_NEW = [
    {
        "id": "subscription_creep",
        "title": "Subscription creep",
        "finding": "You have 4 recurring charges totaling $234.96/mo: Netflix/Spotify/Hulu bundle, Gym membership, Cloud storage, Meal kit delivery.",
        "evidence": ["Subscriptions detected: 4", "Monthly total: $234.96", "Yearly cost: $2819.52"],
        "dollar_impact": 2819.52,
        "subscriptions": [
            {"name": "Netflix/Spotify/Hulu bundle", "amount": 89.99, "occurrences": 12, "avg_gap_days": 30.2},
            {"name": "Gym membership - Equinox", "amount": 79.99, "occurrences": 10, "avg_gap_days": 30.5},
            {"name": "iCloud storage 2TB", "amount": 14.99, "occurrences": 11, "avg_gap_days": 30.1},
            {"name": "HelloFresh meal kit", "amount": 49.99, "occurrences": 8, "avg_gap_days": 31.0},
        ],
        "monthly_total": 234.96,
        "what_this_means": "These charges repeat every month whether you use the service or not. Review each one and cancel anything you haven't used in the last 30 days.",
        "recommended_next_actions": [
            "Open each subscription and check your last login date.",
            "Cancel one subscription you haven't used in 30 days.",
        ],
    },
    {
        "id": "expensive_day_of_week",
        "title": "Your expensive day of the week",
        "finding": "You spend the most on Fridays \u2014 $47.82 avg vs $28.15 overall (70% above average).",
        "evidence": [
            "Average by day: Monday: $22.10, Tuesday: $18.50, Wednesday: $25.30, Thursday: $31.20, Friday: $47.82, Saturday: $35.40, Sunday: $16.75",
            "Cheapest day: Sunday",
        ],
        "dollar_impact": None,
        "by_day": {
            "Monday": 22.10, "Tuesday": 18.50, "Wednesday": 25.30,
            "Thursday": 31.20, "Friday": 47.82, "Saturday": 35.40, "Sunday": 16.75,
        },
        "expensive_day": "Friday",
        "cheapest_day": "Sunday",
        "pct_above_average": 70.0,
        "what_this_means": "Friday is when you're most likely to overspend. Knowing this lets you plan ahead.",
        "recommended_next_actions": [
            "Set a Friday spending cap and check it before buying.",
            "Pre-plan Friday meals or activities to avoid impulse purchases.",
        ],
    },
    {
        "id": "post_payday_surge",
        "title": "Post-payday spending surge",
        "finding": "34.2% of your spending happens within 3 days of getting paid ($1,847.30 of $5,401.20).",
        "evidence": ["Paydays detected: 12", "Post-payday spend: $1847.30", "Total spend: $5401.20", "Surge ratio: 34.2%"],
        "dollar_impact": 1847.30,
        "detected": True,
        "surge_pct": 34.2,
        "what_this_means": "You spend heavily right after payday, which can leave you tight before the next one. This is a common pattern \u2014 awareness is the first step.",
        "recommended_next_actions": [
            "Wait 24 hours after payday before any non-essential purchase.",
            "Auto-transfer savings on payday before you can spend it.",
        ],
    },
    {
        "id": "worry_timeline",
        "title": "When you worry most (AI conversations x spending)",
        "finding": "You mentioned financial/emotional worries 14 times in AI conversations. Peak worry: week 2025-07 ($89.99 spent that week).",
        "evidence": [
            "Total worry mentions: 14",
            "Weeks with worry signals: 8",
            "Sources: ChatGPT/Claude conversation exports cross-referenced with spending data.",
        ],
        "dollar_impact": None,
        "timeline": [
            {"year_week": "2024-50", "worry_mentions": 2, "discretionary_spend": 0.0},
            {"year_week": "2024-51", "worry_mentions": 3, "discretionary_spend": 0.0},
            {"year_week": "2025-02", "worry_mentions": 1, "discretionary_spend": 0.0},
            {"year_week": "2025-04", "worry_mentions": 2, "discretionary_spend": 0.0},
            {"year_week": "2025-06", "worry_mentions": 1, "discretionary_spend": 89.99},
            {"year_week": "2025-07", "worry_mentions": 3, "discretionary_spend": 89.99},
            {"year_week": "2025-08", "worry_mentions": 1, "discretionary_spend": 85.0},
            {"year_week": "2025-09", "worry_mentions": 1, "discretionary_spend": 85.0},
        ],
        "peak_worry_week": "2025-07",
        "total_worry_mentions": 14,
        "what_this_means": "Your AI conversations reveal when stress peaks. Overlaying this with spending shows whether worry translates into spending changes \u2014 something no single data source can show alone.",
        "recommended_next_actions": [
            "During high-worry weeks, set a 24-hour rule on discretionary purchases.",
            "Use your AI assistant to journal about financial stress instead of spending through it.",
        ],
    },
]

P05_NEW = [
    {
        "id": "subscription_creep",
        "title": "Subscription creep",
        "finding": "You have 6 recurring charges totaling $187.94/mo: Adobe Creative Cloud, Figma Pro, Notion, Spotify, ChatGPT Plus, GitHub Copilot.",
        "evidence": ["Subscriptions detected: 6", "Monthly total: $187.94", "Yearly cost: $2255.28"],
        "dollar_impact": 2255.28,
        "subscriptions": [
            {"name": "Adobe Creative Cloud", "amount": 59.99, "occurrences": 11, "avg_gap_days": 30.3},
            {"name": "Figma Professional", "amount": 45.00, "occurrences": 10, "avg_gap_days": 30.1},
            {"name": "Notion Team", "amount": 20.00, "occurrences": 12, "avg_gap_days": 30.0},
            {"name": "Spotify Premium", "amount": 12.99, "occurrences": 12, "avg_gap_days": 30.2},
            {"name": "ChatGPT Plus", "amount": 29.99, "occurrences": 9, "avg_gap_days": 30.5},
            {"name": "GitHub Copilot", "amount": 19.97, "occurrences": 11, "avg_gap_days": 30.1},
        ],
        "monthly_total": 187.94,
        "what_this_means": "As a freelancer, tool subscriptions add up fast. Are you billing clients enough to cover these overhead costs?",
        "recommended_next_actions": [
            "Check which tools you actually used in the last 30 days.",
            "Bundle tool costs into your client rate \u2014 these are business expenses.",
        ],
    },
    {
        "id": "expensive_day_of_week",
        "title": "Your expensive day of the week",
        "finding": "You spend the most on Wednesdays \u2014 $52.40 avg vs $31.60 overall (66% above average).",
        "evidence": [
            "Average by day: Monday: $28.50, Tuesday: $24.30, Wednesday: $52.40, Thursday: $35.10, Friday: $38.20, Saturday: $22.90, Sunday: $19.80",
            "Cheapest day: Sunday",
        ],
        "dollar_impact": None,
        "by_day": {
            "Monday": 28.50, "Tuesday": 24.30, "Wednesday": 52.40,
            "Thursday": 35.10, "Friday": 38.20, "Saturday": 22.90, "Sunday": 19.80,
        },
        "expensive_day": "Wednesday",
        "cheapest_day": "Sunday",
        "pct_above_average": 66.0,
        "what_this_means": "Wednesday is when you're most likely to overspend. As a freelancer, this might correlate with mid-week burnout.",
        "recommended_next_actions": [
            "Set a Wednesday spending cap and check it before buying.",
            "Pre-plan Wednesday meals or activities to avoid impulse purchases.",
        ],
    },
    {
        "id": "post_payday_surge",
        "title": "Post-payday spending surge",
        "finding": "No significant post-payday surge \u2014 18.5% of spending is in the 3-day post-payday window.",
        "evidence": ["Paydays detected: 7", "Post-payday spend: $892.40", "Total spend: $4824.00", "Surge ratio: 18.5%"],
        "dollar_impact": None,
        "detected": False,
        "surge_pct": 18.5,
        "what_this_means": "Your spending is relatively evenly distributed across the pay cycle. As a freelancer with irregular income, this is a good sign.",
        "recommended_next_actions": [
            "Keep the discipline \u2014 irregular income makes post-payday splurges riskier.",
            "Auto-transfer 20% of each invoice payment to savings on receipt.",
        ],
    },
    {
        "id": "worry_timeline",
        "title": "When you worry most (AI conversations x spending)",
        "finding": "You mentioned financial/emotional worries 22 times in AI conversations. Peak worry: week 2025-04 ($45.00 spent that week).",
        "evidence": [
            "Total worry mentions: 22",
            "Weeks with worry signals: 11",
            "Sources: ChatGPT/Claude conversation exports cross-referenced with spending data.",
        ],
        "dollar_impact": None,
        "timeline": [
            {"year_week": "2024-46", "worry_mentions": 2, "discretionary_spend": 30.00},
            {"year_week": "2024-48", "worry_mentions": 3, "discretionary_spend": 0.0},
            {"year_week": "2024-50", "worry_mentions": 1, "discretionary_spend": 25.00},
            {"year_week": "2025-01", "worry_mentions": 2, "discretionary_spend": 0.0},
            {"year_week": "2025-03", "worry_mentions": 3, "discretionary_spend": 40.00},
            {"year_week": "2025-04", "worry_mentions": 4, "discretionary_spend": 45.00},
            {"year_week": "2025-05", "worry_mentions": 2, "discretionary_spend": 55.00},
            {"year_week": "2025-06", "worry_mentions": 1, "discretionary_spend": 35.00},
            {"year_week": "2025-08", "worry_mentions": 2, "discretionary_spend": 60.00},
            {"year_week": "2025-09", "worry_mentions": 1, "discretionary_spend": 20.00},
            {"year_week": "2025-10", "worry_mentions": 1, "discretionary_spend": 0.0},
        ],
        "peak_worry_week": "2025-04",
        "total_worry_mentions": 22,
        "what_this_means": "Your AI conversations reveal when stress peaks. Client stress and ADHD-related worries cluster in specific weeks, and spending follows.",
        "recommended_next_actions": [
            "During high-worry weeks, set a 24-hour rule on discretionary purchases.",
            "Use your AI assistant to journal about financial stress instead of spending through it.",
        ],
    },
]

PERSONA_MAP = {"p01": P01_NEW, "p05": P05_NEW}

for pid, new_insights in PERSONA_MAP.items():
    path = ROOT / "outputs" / f"insights_{pid}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    data["insights"] = [i for i in data["insights"] if i["id"] not in REMOVE_IDS]
    data["insights"].extend(new_insights)
    data["metric_layer_version"] = "actionable_v2"

    # Validate
    seen: set[str] = set()
    for i in data["insights"]:
        assert i["id"] not in seen, f"duplicate: {i['id']}"
        seen.add(i["id"])
        for f in ("id", "title", "finding", "evidence", "dollar_impact"):
            assert f in i, f"missing {f} in {i['id']}"

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{pid}: wrote {len(data['insights'])} insights -> {path}")
