from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "v1_locked":
        st.error("Cached insights are not on the locked schema. Regenerate cache with `save_insights`.")
        st.stop()
    return payload


def _find_insight(payload: dict[str, Any], insight_id: str) -> dict[str, Any] | None:
    for item in payload.get("insights", []):
        if item.get("id") == insight_id:
            return item
    return None


def _fmt_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def _render_data_story(consent: dict[str, Any]) -> None:
    st.subheader("Data Story")
    st.markdown(
        "- **Where data comes from:** exported synthetic records for calendar, transactions, conversations, email, and social logs.\n"
        "- **Who owns it:** the persona owner controls the exported files and when they are shared.\n"
        "- **What is computed:** stress index, discretionary spend trends, and cross-source weekly insights.\n"
        "- **Why multi-source matters:** one source alone misses behavior links that appear only when calendar + money + language signals are combined."
    )

    st.markdown("**Consent & Privacy**")
    st.info(
        "Local processing only. This demo runs in synthetic mode. No raw records are sent to the LLM; only structured insights JSON is used for chat."
    )
    if consent:
        st.caption(
            f"Dataset: {consent.get('dataset_type', 'unknown')} | Retention: {consent.get('retention', 'unknown')}"
        )


def _spike_week_label(spike: dict[str, Any]) -> str:
    return str(spike.get("year_week") or "Unknown")


def _spike_spend(spike: dict[str, Any]) -> float:
    try:
        return float(spike.get("weekly_discretionary_total", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _spike_stress(spike: dict[str, Any]) -> float:
    try:
        value = spike.get("prior_week_stress")
        return 0.0 if value is None else float(value)
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
            marker_color="#E76F51",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=stress,
            name="Prior Week Stress",
            mode="lines+markers",
            line={"color": "#264653", "width": 3},
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=360,
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
            threshold_math = spike.get("threshold_math") or {}
            st.write(
                "Threshold math:",
                {
                    "week_spend": threshold_math.get("week_spend"),
                    "mean": threshold_math.get("mean"),
                    "std": threshold_math.get("std"),
                    "threshold": threshold_math.get("threshold"),
                    "prior_week_stress": threshold_math.get("prior_week_stress"),
                },
            )
            st.caption(spike.get("evidence", "No evidence text available."))

            left, right = st.columns(2)
            with left:
                st.markdown("**Top 3 discretionary transactions**")
                txns = spike.get("top_transactions") or []
                if txns:
                    for tx in txns:
                        st.write(
                            f"- {tx.get('date', 'N/A')} | {tx.get('text', 'Transaction')} | "
                            f"${_fmt_number(tx.get('amount'), 2)} | {', '.join(tx.get('tags', []))}"
                        )
                else:
                    st.write("No discretionary transactions matched for this week.")

            with right:
                st.markdown("**Up to 3 related calendar events**")
                events = spike.get("calendar_events") or []
                if events:
                    for event in events:
                        st.write(
                            f"- {event.get('date', 'N/A')} | {event.get('title', 'Event')} | "
                            f"{', '.join(event.get('tags', []))}"
                        )
                else:
                    st.write("No calendar evidence was linked for this week.")


def _render_actions(insight: dict[str, Any]) -> None:
    actions = insight.get("recommended_next_actions") or []
    if actions:
        st.markdown("**Recommended next action**")
        for action in actions:
            st.write(f"- {action}")


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
    st.sidebar.caption("All data is synthetic and processed locally.")

    data = _load_insights(selected)

    profile_name = data.get("profile_name") or PERSONA_OPTIONS[selected].split(" — ")[0]
    st.title(profile_name)
    st.caption("This is what your data can tell you when insights are grounded in your own records.")

    stress_insight = _find_insight(data, "stress_spend_correlation")
    theme_insight = _find_insight(data, "top_anxiety_themes")
    goal_insight = _find_insight(data, "months_to_goal")
    rate_insight = _find_insight(data, "invoice_rate_risk")

    stress_corr = None if not stress_insight else stress_insight.get("correlation_coefficient")
    months_to_goal = None if not goal_insight else goal_insight.get("months_to_goal")
    top_themes = [] if not theme_insight else [f"{t.get('theme')}" for t in (theme_insight.get("top_themes") or [])[:3]]

    c1, c2, c3 = st.columns(3)
    c1.metric("Stress → Spend Correlation", _fmt_number(stress_corr, 2))
    c1.caption((stress_insight or {}).get("what_this_means", "No correlation interpretation available."))

    c2.metric("Months to Savings Goal", _fmt_number(months_to_goal, 1))
    c2.caption((goal_insight or {}).get("what_this_means", "Savings timeline unavailable in current profile."))

    c3.metric("Top Anxiety Themes", ", ".join(top_themes) if top_themes else "None detected")
    c3.caption((theme_insight or {}).get("what_this_means", "Theme extraction unavailable."))

    st.subheader("Stress vs Discretionary Spend")
    if not stress_insight:
        st.error("Stress/spend insight missing from cache. Regenerate insights.")
    else:
        st.write(stress_insight.get("finding", "No finding available."))
        for ev in stress_insight.get("evidence", []):
            st.write(f"- {ev}")
        spike_weeks = stress_insight.get("spike_weeks") or []
        if spike_weeks:
            _render_spike_chart(spike_weeks)
            _render_spike_expanders(spike_weeks)
        else:
            if stress_insight.get("insufficient_variance"):
                st.info(
                    "Not enough week-to-week variation to isolate spike weeks yet. Keep collecting more varied weeks and rerun insights."
                )
            else:
                st.info("No spike weeks crossed threshold in this run. Focus on trend and recommendation bullets below.")
        _render_actions(stress_insight)

    st.subheader("Recurring Themes")
    if theme_insight:
        st.write(theme_insight.get("finding"))
        for ev in theme_insight.get("evidence", []):
            st.write(f"- {ev}")
        _render_actions(theme_insight)

    st.subheader("Savings Goal Velocity")
    if goal_insight:
        st.write(goal_insight.get("finding"))
        for ev in goal_insight.get("evidence", []):
            st.write(f"- {ev}")
        _render_actions(goal_insight)

    if selected == "p05" and rate_insight:
        st.subheader("Freelancer Rate Signal")
        st.write(rate_insight.get("finding"))
        for ev in rate_insight.get("evidence", []):
            st.write(f"- {ev}")
        matches = rate_insight.get("matches") or []
        if matches:
            for item in matches:
                st.write(
                    f"- Date: {item.get('date', 'N/A')} | Implied Rate: ${_fmt_number(item.get('implied_hourly_rate'), 2)}/hr"
                )
        else:
            st.info("No low-rate matches were found in the current cache.")
        _render_actions(rate_insight)

    _render_data_story(data.get("consent", {}))

    st.subheader("Ask About Your Data")
    st.caption("Grounded in precomputed insights only.")

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
