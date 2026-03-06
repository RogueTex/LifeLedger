from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "demo_backups"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_panels(persona_id: str) -> dict:
    payload = json.loads((ROOT / "outputs" / f"insights_{persona_id}.json").read_text(encoding="utf-8"))
    insights = {item["id"]: item for item in payload.get("insights", [])}

    stress = insights.get("stress_spend_correlation", {})
    goals = insights.get("months_to_goal", {})
    themes = insights.get("top_anxiety_themes", {})
    rate = insights.get("invoice_rate_risk", {})

    return {
        "persona": persona_id,
        "profile_name": payload.get("profile_name"),
        "critical_panels": {
            "kpi_summary": {
                "correlation_coefficient": stress.get("correlation_coefficient"),
                "months_to_goal": goals.get("months_to_goal"),
                "top_themes": [t.get("theme") for t in themes.get("top_themes", [])[:3]],
            },
            "stress_spike_panel": {
                "finding": stress.get("finding"),
                "evidence": stress.get("evidence", []),
                "spike_weeks": stress.get("spike_weeks", []),
            },
            "rate_signal_panel": {
                "finding": rate.get("finding"),
                "evidence": rate.get("evidence", []),
                "matches": rate.get("matches", []),
            },
            "consent_panel": payload.get("consent", {}),
        },
    }


for pid in ("p01", "p05"):
    backup = extract_panels(pid)
    out_path = OUT_DIR / f"backup_{pid}.json"
    out_path.write_text(json.dumps(backup, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
