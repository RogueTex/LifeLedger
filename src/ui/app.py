from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.insights.narrative_gen import generate_narrative


PERSONA_OPTIONS = {
    "p01": "Jordan Lee — Burnout + Home Savings",
    "p05": "Theo Nakamura — Freelancer Business Brain",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_insights(persona_id: str) -> dict[str, Any]:
    path = _project_root() / "outputs" / f"insights_{persona_id}.json"
    if not path.exists():
        st.error(
            f"Missing `{path.name}`. Run `from src.insights.insight_engine import save_insights; "
            f"save_insights(\"{persona_id}\")` first."
        )
        st.stop()
    return json.loads(path.read_text(encoding="utf-8"))


def _find_insight(payload: dict[str, Any], *keys: str) -> dict[str, Any] | None:
    insights = payload.get("insights", [])
    wanted = set(keys)
    for item in insights:
        item_key = item.get("id") or item.get("type")
        if item_key in wanted:
            return item
    return None


def _fmt_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def _extract_top_themes(themes_insight: dict[str, Any] | None) -> list[str]:
    if not themes_insight:
        return []

    if "value" in themes_insight and isinstance(themes_insight["value"], list):
        rows = themes_insight["value"]
    else:
        rows = themes_insight.get("anxiety_themes") or themes_insight.get("top_themes") or []

    out: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            name = row.get("theme") or row.get("name") or row.get("tag")
            if name:
                out.append(str(name))
        elif isinstance(row, str):
            out.append(row)
    return out[:3]


def _extract_months_to_goal(goal_insight: dict[str, Any] | None) -> Any:
    if not goal_insight:
        return None
    if isinstance(goal_insight.get("value"), dict):
        return goal_insight["value"].get("months_to_goal")
    return goal_insight.get("months_to_goal")


def _extract_stress_payload(stress_insight: dict[str, Any] | None) -> dict[str, Any]:
    if not stress_insight:
        return {}
    if isinstance(stress_insight.get("value"), dict):
        return stress_insight["value"]
    return stress_insight


def _spike_week_label(spike: dict[str, Any]) -> str:
    return str(spike.get("week") or spike.get("year_week") or "Unknown")


def _spike_spend(spike: dict[str, Any]) -> float:
    value = spike.get("discretionary_spend", spike.get("weekly_discretionary_total", 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _spike_stress(spike: dict[str, Any]) -> float:
    value = spike.get("prior_week_stress", 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _render_spike_chart(spike_weeks: list[dict[str, Any]]) -> None:
    labels = [_spike_week_label(w) for w in spike_weeks]
    spend = [_spike_spend(w) for w in spike_weeks]
    stress = [_spike_stress(w) for w in spike_weeks]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=labels,
            y=spend,
            name="Discretionary Spend",
            marker_color="#FF6B6B",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=stress,
            name="Prior Week Stress",
            mode="lines+markers",
            line={"color": "#F59E0B", "width": 3},
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=380,
        template="plotly_white",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        legend={"orientation": "h", "y": 1.1, "x": 0.0},
    )
    fig.update_yaxes(title_text="Discretionary Spend ($)", secondary_y=False)
    fig.update_yaxes(title_text="Prior Week Stress", range=[0, 1], secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def _render_spike_expanders(spike_weeks: list[dict[str, Any]]) -> None:
    for spike in spike_weeks:
        week = _spike_week_label(spike)
        spend = _spike_spend(spike)
        with st.expander(f"Week {week} — ${spend:,.2f}"):
            left, right = st.columns(2)

            txns = spike.get("top_transactions") or []
            events = spike.get("calendar_events") or []

            with left:
                st.markdown("**Top Transactions**")
                if txns:
                    for tx in txns:
                        text = tx.get("text") or tx.get("description") or tx.get("merchant") or "Transaction"
                        amount = tx.get("amount")
                        tags = tx.get("tags") or []
                        tag_text = ", ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
                        amount_text = f"${float(amount):,.2f}" if amount is not None else "$0.00"
                        st.write(f"- {text} | {amount_text} | {tag_text}")
                else:
                    if spike.get("evidence"):
                        st.write(spike["evidence"])
                    else:
                        st.write("No transaction breakdown available.")

            with right:
                st.markdown("**Calendar Events**")
                if events:
                    for event in events:
                        text = event.get("text") or event.get("title") or event.get("subject") or "Event"
                        ts = event.get("ts") or event.get("date") or ""
                        st.write(f"- {text} {f'({ts})' if ts else ''}")
                else:
                    st.write("No calendar event details available.")


def main() -> None:
    st.set_page_config(page_title="LifeLedger", page_icon="💰", layout="wide")

    st.sidebar.title("💰 LifeLedger")
    st.sidebar.caption("Connect your money to your life.")

    selected = st.sidebar.selectbox(
        "Persona",
        options=list(PERSONA_OPTIONS.keys()),
        format_func=lambda pid: PERSONA_OPTIONS[pid],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("All data is 100% synthetic. Processed locally.")

    data = _load_insights(selected)

    profile_name = data.get("profile_name") or PERSONA_OPTIONS[selected].split(" — ")[0]
    st.title(profile_name)
    st.caption("This is what your data can tell you — if you own it.")

    stress_insight = _find_insight(data, "stress_spend", "stress_spend_correlation")
    theme_insight = _find_insight(data, "recurring_themes", "top_anxiety_themes")
    goal_insight = _find_insight(data, "goal_velocity", "months_to_goal")
    rate_insight = _find_insight(data, "undercharging_alert", "invoice_rate_risk")

    stress_payload = _extract_stress_payload(stress_insight)
    correlation = stress_payload.get("correlation") if "correlation" in stress_payload else stress_payload.get("correlation_coefficient")
    months_to_goal = _extract_months_to_goal(goal_insight)
    top_themes = _extract_top_themes(theme_insight)

    c1, c2, c3 = st.columns(3)
    c1.metric("Stress → Spend Correlation", _fmt_number(correlation, 2))
    c2.metric("Months to Savings Goal", _fmt_number(months_to_goal, 1))
    c3.metric("Top Anxiety Themes", ", ".join(top_themes) if top_themes else "N/A")

    spike_weeks = stress_payload.get("spike_weeks") or stress_payload.get("evidence") or []
    st.subheader("Stress vs Discretionary Spend")
    if spike_weeks:
        _render_spike_chart(spike_weeks)
        _render_spike_expanders(spike_weeks)
    else:
        st.info("No spike weeks detected in the current cached insights.")

    if selected == "p05" and rate_insight:
        payload = rate_insight.get("value") if isinstance(rate_insight.get("value"), dict) else rate_insight
        flagged = bool(payload.get("flagged"))
        matches = payload.get("matches") or []
        if flagged:
            st.warning("Undercharging alert: detected implied hourly rate below $65/hr baseline.")
            for item in matches:
                st.write(
                    f"- Date: {item.get('date', 'N/A')} | Implied Rate: ${_fmt_number(item.get('implied_hourly_rate'), 2)}/hr"
                )
        else:
            st.warning("Freelancer scan complete: no undercharging alert detected in current cache.")

    st.subheader("💬 Ask About Your Data")
    st.caption("Grounded in precomputed insights — no raw data sent to any API.")

    chat_key = f"chat_history_{selected}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask a question about your insights...")
    if question:
        st.session_state[chat_key].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        try:
            answer = generate_narrative(question, data)
        except Exception as exc:
            err = str(exc)
            if "api" in err.lower() or "key" in err.lower() or "OPENAI_API_KEY" in err:
                answer = "Could not call OpenAI. Set `OPENAI_API_KEY` in `.env` and try again."
            else:
                answer = f"Failed to generate response: {err}"

        st.session_state[chat_key].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)


if __name__ == "__main__":
    main()
