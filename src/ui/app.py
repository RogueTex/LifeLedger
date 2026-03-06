from __future__ import annotations

import json
import os
import sys
from html import escape
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


def _inject_global_style() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0a0a0f;
          --card: #13131a;
          --accent: #6c63ff;
          --warn: #ff6b6b;
          --positive: #00d4aa;
          --text: #f2f2f7;
          --muted: #888;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
          background: var(--bg);
          color: var(--text);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        [data-testid="stMainBlockContainer"], .block-container {
          max-width: 1180px;
          margin-left: auto;
          margin-right: auto;
          padding-top: 0;
          padding-right: 1rem;
          padding-left: 1rem;
          padding-bottom: 1.5rem;
        }

        [data-testid="stSidebar"] {
          background: #101018;
          border-right: 1px solid rgba(108, 99, 255, 0.2);
        }

        .hero-wrap {
          padding-top: 0.9rem;
          margin-bottom: 1.1rem;
        }

        .hero-row {
          display: flex;
          align-items: center;
          justify-content: flex-start;
          gap: 1rem;
        }

        .hero-copy {
          min-width: 0;
          flex: 1;
        }

        .hero-title {
          font-size: 2.8rem;
          font-weight: 800;
          line-height: 1.05;
          color: var(--text);
          margin: 0;
        }

        .hero-tagline {
          margin-top: 0.35rem;
          color: #8e8e9a;
          font-size: 1rem;
        }

        .hero-rule {
          margin-top: 0.9rem;
          height: 1px;
          border: 0;
          background: linear-gradient(90deg, #6c63ff, #ff6b6b);
        }

        .metric-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.85rem;
          margin-bottom: 1rem;
        }

        .kpi-card,
        .insight-card,
        .spike-card,
        .chat-shell {
          background: var(--card);
          border: 1px solid rgba(108, 99, 255, 0.2);
          border-radius: 16px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
        }

        .kpi-card {
          padding: 1rem 1rem 0.9rem;
          min-height: 132px;
        }

        .kpi-label {
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-size: 11px;
          color: #8e8ea0;
          margin-bottom: 0.4rem;
        }

        .kpi-value {
          font-size: 2.4rem;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 0.4rem;
        }

        .kpi-detail {
          font-size: 12px;
          color: #8f90a6;
          line-height: 1.35;
        }

        div[data-testid="metric-container"] label,
        div[data-testid="metric-container"] div[data-testid="stMetricLabel"] {
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-size: 11px;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
          font-size: 2.4rem;
          font-weight: 700;
        }

        .section-heading {
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: #9c94ff;
          font-size: 12px;
          margin-top: 0.8rem;
          margin-bottom: 0.55rem;
        }

        .insight-card {
          padding: 0.95rem 1rem;
          margin-bottom: 0.75rem;
        }

        .insight-title {
          text-transform: uppercase;
          letter-spacing: 0.15em;
          font-size: 12px;
          color: #9c94ff;
          margin-bottom: 0.45rem;
        }

        .insight-finding {
          font-size: 18px;
          color: var(--text);
          font-weight: 700;
          margin-bottom: 0.45rem;
        }

        .insight-support {
          font-size: 13px;
          color: var(--muted);
          line-height: 1.45;
          margin-bottom: 0.7rem;
        }

        .pill-row {
          display: flex;
          gap: 0.4rem;
          flex-wrap: wrap;
        }

        .action-pill, .tag-pill {
          background: rgba(108, 99, 255, 0.15);
          border: 1px solid rgba(108, 99, 255, 0.3);
          border-radius: 20px;
          padding: 4px 12px;
          font-size: 12px;
          color: #ddd9ff;
          display: inline-block;
        }

        .tag-pill {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.14);
          color: #b8b8c6;
          padding: 2px 8px;
          font-size: 11px;
        }

        .consent-banner {
          background: rgba(0, 212, 170, 0.08);
          border-left: 3px solid #00d4aa;
          border-radius: 10px;
          padding: 0.75rem 0.9rem;
          color: rgba(225, 255, 249, 0.92);
          font-size: 13px;
          margin-top: 0.55rem;
        }

        .spike-card {
          padding: 0.75rem 0.8rem 0.8rem;
          margin-top: 0.55rem;
        }

        .tx-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 0.5rem;
          align-items: start;
          margin-bottom: 0.6rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          padding-bottom: 0.45rem;
        }

        .tx-merchant {
          color: #f1f1f8;
          font-size: 13px;
          margin-bottom: 0.25rem;
          line-height: 1.35;
        }

        .tx-amount {
          color: var(--warn);
          font-weight: 700;
          font-size: 14px;
          white-space: nowrap;
        }

        .cal-row {
          margin-bottom: 0.55rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          padding-bottom: 0.4rem;
          color: #d5d5e0;
          font-size: 13px;
          line-height: 1.35;
        }

        .chat-shell {
          padding: 0.85rem;
          margin-top: 0.5rem;
        }

        .chat-user {
          margin-left: auto;
          max-width: 78%;
          background: rgba(108, 99, 255, 0.25);
          border: 1px solid rgba(108, 99, 255, 0.35);
          border-radius: 14px 14px 2px 14px;
          padding: 0.6rem 0.75rem;
          color: #eceaff;
          margin-bottom: 0.55rem;
          font-size: 13px;
          line-height: 1.4;
        }

        .chat-assistant {
          margin-right: auto;
          max-width: 82%;
          background: #12121a;
          border-left: 3px solid #00d4aa;
          border-radius: 12px;
          padding: 0.6rem 0.75rem;
          color: #e7fef8;
          margin-bottom: 0.55rem;
          font-size: 13px;
          line-height: 1.45;
          white-space: pre-wrap;
        }

        .typing {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          color: #8de9d2;
          font-size: 12px;
        }

        .typing span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #8de9d2;
          animation: blink 1.2s infinite;
        }

        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes blink {
          0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
          40% { opacity: 1; transform: translateY(-2px); }
        }

        .stChatInput textarea,
        .stTextInput input {
          background: #11111a !important;
          color: #f4f4fc !important;
          border: 1px solid rgba(108, 99, 255, 0.35) !important;
          border-radius: 12px !important;
        }

        .stChatInput textarea:focus,
        .stTextInput input:focus {
          border: 1px solid #6c63ff !important;
          box-shadow: 0 0 0 1px rgba(108, 99, 255, 0.4) !important;
        }

        [data-baseweb="select"] > div {
          background: #11111a !important;
          border: 1px solid rgba(108, 99, 255, 0.35) !important;
          color: #ececff !important;
          border-radius: 10px !important;
        }

        .stAlert, .stInfo, .stWarning {
          background: #151524 !important;
          border: 1px solid rgba(108, 99, 255, 0.25) !important;
          color: #dfdfff !important;
        }

        @media (max-width: 920px) {
          .metric-grid { grid-template-columns: 1fr; }
          .hero-title { font-size: 2.2rem; }
          .hero-row { flex-direction: column; align-items: flex-start; }
          .chat-user, .chat-assistant { max-width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _one_sentence(text: Any) -> str:
    raw = str(text or "").strip()
    if not raw:
        return "No finding available."
    normalized = " ".join(raw.split())
    for sep in (". ", "! ", "? "):
        if sep in normalized:
            return normalized.split(sep, 1)[0].strip() + sep.strip()
    return normalized


def _section_label(name: str) -> None:
    st.markdown(
        f'<div style="font-size:10px; text-transform:uppercase; '
        f'letter-spacing:0.2em; color:#444; margin-bottom:12px;">'
        f"{escape(name)}</div>",
        unsafe_allow_html=True,
    )


def _section_spacer() -> None:
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)


def _gradient_divider() -> None:
    st.markdown(
        '<div style="height:1px; background:linear-gradient('
        'to right, rgba(108,99,255,0.3), rgba(255,107,107,0.3), '
        'rgba(0,0,0,0)); margin:8px 0 24px 0;"></div>',
        unsafe_allow_html=True,
    )


def _render_welcome_gate() -> bool:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        .welcome-stage {
          min-height: 92vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          animation: fade-up 520ms ease;
        }
        .welcome-title {
          font-size: clamp(2.2rem, 6vw, 4.8rem);
          line-height: 1.02;
          font-weight: 800;
          color: #f4f4fc;
          margin: 0 0 1.6rem 0;
          letter-spacing: -0.02em;
        }
        .welcome-logo-wrap {
          width: 160px;
          height: 160px;
          border-radius: 999px;
          display: grid;
          place-items: center;
          position: relative;
          margin-bottom: 1.4rem;
        }
        .welcome-logo-ring {
          position: absolute;
          inset: 0;
          border-radius: 999px;
          background: conic-gradient(from 0deg, #6c63ff, #8d85ff, #ff6b6b, #6c63ff);
          filter: blur(0.3px);
          animation: spin 5.2s linear infinite;
        }
        .welcome-logo-core {
          width: 122px;
          height: 122px;
          border-radius: 999px;
          background: radial-gradient(circle at 32% 28%, #1d1c2b, #0b0b12 70%);
          border: 1px solid rgba(255, 255, 255, 0.08);
          display: grid;
          place-items: center;
          position: relative;
          z-index: 1;
          box-shadow: 0 0 32px rgba(108, 99, 255, 0.25);
        }
        .welcome-logo-text {
          color: #e9e6ff;
          font-size: 1.6rem;
          font-weight: 700;
          letter-spacing: 0.04em;
        }
        .welcome-sub {
          color: #8f8fa1;
          font-size: 0.98rem;
          margin-bottom: 1.4rem;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes fade-up {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        </style>
        <div class="welcome-stage">
          <h1 class="welcome-title">Welcome to LifeLedger</h1>
          <div class="welcome-logo-wrap">
            <div class="welcome-logo-ring"></div>
            <div class="welcome-logo-core"><div class="welcome-logo-text">LL</div></div>
          </div>
          <div class="welcome-sub">Connect your money to your life with grounded insights.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.4, 1, 1.4])
    with c2:
        start_now = st.button("Start Now", use_container_width=True, type="primary", key="welcome_start_now")
        demo = st.button("View Demo", use_container_width=True, key="welcome_demo")

    if start_now:
        st.session_state["entered_app"] = True
        st.session_state["landing_view"] = "your_data"
        st.rerun()
    if demo:
        st.session_state["entered_app"] = True
        st.session_state["landing_view"] = "demo"
        st.rerun()
    return False


def _render_header(profile_name: str, orb_fast: bool) -> None:
    st.markdown(
        f"""
        <div class="hero-wrap">
          <div class="hero-row">
            <div class="hero-copy">
              <h1 class="hero-title">{escape(profile_name)}</h1>
              <div class="hero-tagline">This is what your data can tell you.</div>
            </div>
          </div>
          <hr class="hero-rule" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_orb_overlay() -> None:
    st.markdown(
        """
<style>
.orb-container {
  position: fixed;
  top: 60px;
  right: 40px;
  width: 100px;
  height: 100px;
  z-index: 999;
}
.orb-core {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 48px; height: 48px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%,
    #a78bfa, #6c63ff 40%, #ff6b6b 80%);
  box-shadow: 0 0 30px rgba(108,99,255,0.6),
              0 0 60px rgba(108,99,255,0.2);
  animation: breathe 3s ease-in-out infinite;
}
.orb-ring {
  position: absolute;
  top: 50%; left: 50%;
  border-radius: 50%;
  border: 1px solid rgba(108,99,255,0.5);
  transform: translate(-50%, -50%) scale(1);
  animation: pulse-ring 2.5s ease-out infinite;
}
.orb-ring:nth-child(2) { animation-delay: 0.6s; }
.orb-ring:nth-child(3) { animation-delay: 1.2s; }
.orb-ring:nth-child(2),
.orb-ring:nth-child(3),
.orb-ring:nth-child(4) {
  width: 48px; height: 48px;
}
@keyframes pulse-ring {
  0%   { transform: translate(-50%,-50%) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%,-50%) scale(2.8); opacity: 0; }
}
@keyframes breathe {
  0%, 100% { transform: translate(-50%,-50%) scale(0.95); }
  50%       { transform: translate(-50%,-50%) scale(1.05); }
}
</style>
<div class="orb-container">
  <div class="orb-ring"></div>
  <div class="orb-ring"></div>
  <div class="orb-ring"></div>
  <div class="orb-core"></div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_metric_card(label: str, value: str, detail: str, color: str) -> str:
    return f"""
    <div style="background:#13131a;
    border:1px solid rgba(108,99,255,0.2);
    border-radius:12px;
    padding:20px 24px;
    min-height:0;">
      <div style="font-size:11px; text-transform:uppercase;
      letter-spacing:0.12em; color:#666; margin-bottom:8px;">
        {escape(label)}
      </div>
      <div style="font-size:2rem; font-weight:800;
      color:{color}; line-height:1.1;">
        {escape(value)}
      </div>
      <div style="font-size:12px; color:#666; margin-top:6px;">
        {escape(detail)}
      </div>
    </div>
    """


def _render_kpi_row(stress_insight: dict[str, Any] | None, goal_insight: dict[str, Any] | None, theme_insight: dict[str, Any] | None) -> None:
    stress_corr = None if not stress_insight else stress_insight.get("correlation_coefficient")
    months_to_goal = None if not goal_insight else goal_insight.get("months_to_goal")
    top_themes = [] if not theme_insight else [str(t.get("theme")) for t in (theme_insight.get("top_themes") or [])[:3]]

    corr_value = _fmt_number(stress_corr, 2)
    months_value = _fmt_number(months_to_goal, 1)
    themes_value = ", ".join(top_themes) if top_themes else "None detected"

    corr_detail = (stress_insight or {}).get("what_this_means", "No correlation interpretation available.")
    months_detail = (goal_insight or {}).get("what_this_means", "Savings timeline unavailable in current profile.")
    themes_detail = (theme_insight or {}).get("what_this_means", "Theme extraction unavailable.")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(
            _render_metric_card("Stress to Spend Correlation", corr_value, corr_detail, "#6c63ff"),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _render_metric_card("Months to Savings Goal", months_value, months_detail, "#00d4aa"),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            _render_metric_card("Top Anxiety Themes", themes_value, themes_detail, "#ff6b6b"),
            unsafe_allow_html=True,
        )


def _render_actions_pills(actions: list[str]) -> str:
    if not actions:
        return ""
    pills = "".join(f'<span class="action-pill">{escape(a)}</span>' for a in actions)
    return f'<div class="pill-row">{pills}</div>'


def _render_insight_card(section_title: str, insight: dict[str, Any], support_override: str | None = None) -> None:
    finding = _one_sentence(insight.get("finding"))
    evidence = insight.get("evidence") or []
    support = support_override if support_override is not None else (str(evidence[0]) if evidence else "No supporting detail available.")
    actions = insight.get("recommended_next_actions") or []

    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">{escape(section_title)}</div>
          <div class="insight-finding">{escape(finding)}</div>
          <div class="insight-support">{escape(support)}</div>
          {_render_actions_pills([str(a) for a in actions])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_data_story(consent: dict[str, Any]) -> None:
    story_summary = (
        "Exported synthetic records across calendar, transactions, conversations, email, and social logs are fused "
        "to compute stress patterns, discretionary spend trends, and cross-source weekly insights."
    )
    story_detail = (
        "Multi-source linkage matters because single-source views miss behavioral links that appear only when "
        "calendar pressure, money movement, and language signals are combined."
    )

    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">Data Story</div>
          <div class="insight-finding">{escape(story_summary)}</div>
          <div class="insight-support">{escape(story_detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dataset = consent.get("dataset_type", "unknown") if consent else "unknown"
    retention = consent.get("retention", "unknown") if consent else "unknown"
    consent_text = (
        "Local processing only. This demo runs in synthetic mode. No raw records are sent to the LLM; only structured "
        f"insights JSON is used for chat. Dataset: {dataset} | Retention: {retention}"
    )
    st.markdown(
        f'<div class="consent-banner">🔒 {escape(consent_text)}</div>',
        unsafe_allow_html=True,
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


def _render_spike_chart(spike_weeks: list[dict[str, Any]], weekly_spend_df: list[dict[str, Any]]) -> None:
    if not weekly_spend_df:
        return

    spike_year_weeks = {str(row.get("year_week")) for row in spike_weeks}
    weeks = [str(row.get("year_week")) for row in weekly_spend_df]
    spend = [float(row.get("weekly_discretionary_total", 0.0) or 0.0) for row in weekly_spend_df]
    stress_smooth = []
    for row in weekly_spend_df:
        value = row.get("stress_smooth")
        if value is None:
            value = row.get("weekly_stress_avg")
        try:
            stress_smooth.append(float(value) if value is not None else 0.0)
        except (TypeError, ValueError):
            stress_smooth.append(0.0)

    spike_x: list[str] = []
    spike_y: list[float] = []
    for row in weekly_spend_df:
        week = str(row.get("year_week"))
        if week in spike_year_weeks:
            spike_x.append(week)
            spike_y.append(float(row.get("weekly_discretionary_total", 0.0) or 0.0))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=spend,
            mode="lines+markers",
            line={"color": "#ff6b6b", "width": 2},
            marker={"size": 6},
            fill="tozeroy",
            fillcolor="rgba(255,107,107,0.1)",
            name="Discretionary Spend",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=stress_smooth,
            mode="lines",
            line={"color": "#6c63ff", "width": 2, "dash": "dot"},
            name="Stress Score",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=spike_x,
            y=spike_y,
            mode="markers",
            marker={
                "symbol": "circle",
                "size": 14,
                "color": "#ff6b6b",
                "line": {"color": "white", "width": 2},
            },
            name="Spike Week",
        ),
        secondary_y=False,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,13,26,0.8)",
        height=300,
        margin={"l": 40, "r": 40, "t": 20, "b": 40},
        legend={"orientation": "h", "y": -0.2, "font": {"color": "#888"}},
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", tickfont={"color": "#888"})
    fig.update_yaxes(
        title_text="Spend ($)",
        gridcolor="rgba(255,255,255,0.05)",
        tickfont={"color": "#888"},
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Stress",
        overlaying="y",
        side="right",
        range=[0, 1.2],
        gridcolor="rgba(0,0,0,0)",
        secondary_y=True,
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_spike_details(stress_insight: dict[str, Any]) -> None:
    spike_weeks = stress_insight.get("spike_weeks") or []
    if not spike_weeks:
        if stress_insight.get("insufficient_variance"):
            st.info("Not enough week-to-week variation to isolate spike weeks yet.")
        else:
            st.info("No spike weeks crossed threshold in this run.")
        return

    top_spikes = sorted(spike_weeks, key=_spike_spend, reverse=True)[:3]
    for spike in top_spikes:
        week = escape(_spike_week_label(spike))
        spend = _fmt_number(_spike_spend(spike), 2)
        stress = _fmt_number(spike.get("prior_week_stress"), 2)

        txns = spike.get("top_transactions") or []
        transaction_rows: list[str] = []
        for tx in txns:
            text = escape(str(tx.get("text", "Transaction")))
            amount = _fmt_number(tx.get("amount"), 2)
            transaction_rows.append(
                f'<div style="display:flex; justify-content:space-between; '
                f'padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#ddd; font-size:13px;">{text}</span>'
                f'<span style="color:#ff6b6b; font-weight:600;">${amount}</span>'
                f"</div>"
            )
        if not transaction_rows:
            transaction_rows.append(
                '<div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05); '
                'color:#aaa; font-size:13px;">No discretionary transactions matched.</div>'
            )

        events = spike.get("calendar_events") or []
        calendar_rows: list[str] = []
        for event in events:
            title = str(event.get("title", "Event"))
            date = str(event.get("date", "N/A"))
            event_text = escape(f"{date} | {title}")
            calendar_rows.append(
                f'<div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05); '
                f'color:#aaa; font-size:13px;">📅 {event_text}</div>'
            )
        if not calendar_rows:
            calendar_rows.append(
                '<div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05); '
                'color:#aaa; font-size:13px;">📅 No calendar evidence linked.</div>'
            )

        st.markdown(
            f"""
            <div style="background:#13131a; border:1px solid rgba(255,107,107,0.3);
            border-radius:12px; padding:20px; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between;
              align-items:center; margin-bottom:16px;">
                <span style="color:#ff6b6b; font-weight:700; font-size:16px;">
                  🔴 {week}</span>
                <span style="color:#888; font-size:13px;">
                  ${spend} spent · prior stress {stress}</span>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                <div>
                  <div style="color:#888; font-size:11px;
                  text-transform:uppercase; letter-spacing:0.1em;
                  margin-bottom:8px;">Transactions</div>
                  {"".join(transaction_rows)}
                </div>
                <div>
                  <div style="color:#888; font-size:11px;
                  text-transform:uppercase; letter-spacing:0.1em;
                  margin-bottom:8px;">Calendar</div>
                  {"".join(calendar_rows)}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_resilience_panel(
    stability_insight: dict[str, Any] | None,
    volatility_insight: dict[str, Any] | None,
    liquidity_insight: dict[str, Any] | None,
    regret_insight: dict[str, Any] | None,
    decomposition_insight: dict[str, Any] | None,
    behavioral_overlay: bool,
    macro_overlay: bool,
) -> None:
    if not stability_insight:
        return

    overlay_scores = stability_insight.get("overlay_scores") or {}
    baseline_score = overlay_scores.get("baseline_without_overlays", stability_insight.get("stability_score"))

    if behavioral_overlay and macro_overlay:
        adjusted_score = overlay_scores.get("with_behavioral_and_macro", stability_insight.get("stability_score_with_macro"))
    elif behavioral_overlay and not macro_overlay:
        adjusted_score = overlay_scores.get("with_behavioral_only", stability_insight.get("stability_score"))
    elif (not behavioral_overlay) and macro_overlay:
        adjusted_score = overlay_scores.get("with_macro_only", stability_insight.get("stability_score_with_macro"))
    else:
        adjusted_score = baseline_score

    volatility_value = None if not volatility_insight else volatility_insight.get("volatility_index")
    runway_days = None if not liquidity_insight else liquidity_insight.get("liquidity_runway_days")
    regret_value = None if not regret_insight else regret_insight.get("regret_risk_signal")

    st.markdown(
        f'<div class="insight-support" style="margin-bottom:0.55rem;">'
        f'Baseline score excludes behavioral and macro overlays. Current adjusted score reflects toggles: '
        f'behavioral={behavioral_overlay}, macro={macro_overlay}.'
        f"</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Baseline Stability", _fmt_number(baseline_score, 1))
    col2.metric("Adjusted Stability", _fmt_number(adjusted_score, 1))
    col3.metric("Volatility Index", _fmt_number(volatility_value, 1))
    col4.metric("Runway (days)", _fmt_number(runway_days, 1))
    st.caption(f"Regret risk signal: {_fmt_number(regret_value, 1)} / 100")

    decomposition = dict((decomposition_insight or {}).get("decomposition_percentages") or {})
    if decomposition:
        if not behavioral_overlay:
            decomposition["behavioral"] = 0.0
        if not macro_overlay:
            decomposition["macro_pressure"] = 0.0
        decomposition_rows = [
            ("Behavioral", float(decomposition.get("behavioral", 0.0))),
            ("Structural Fixed Load", float(decomposition.get("structural_fixed_load", 0.0))),
            ("Income Instability", float(decomposition.get("income_instability", 0.0))),
            ("Macro Pressure", float(decomposition.get("macro_pressure", 0.0))),
        ]
        labels = [row[0] for row in decomposition_rows]
        values = [row[1] for row in decomposition_rows]
        fig = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=["#6c63ff", "#ff6b6b", "#00d4aa", "#f59e0b"],
                text=[f"{v:.1f}%" for v in values],
                textposition="outside",
            )
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,13,26,0.8)",
            height=280,
            margin={"l": 40, "r": 30, "t": 10, "b": 30},
            xaxis_title="Contribution (%)",
            yaxis_title="",
        )
        fig.update_xaxes(range=[0, max(100.0, max(values) * 1.25)], gridcolor="rgba(255,255,255,0.06)")
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    levers = list((decomposition_insight or {}).get("top_structural_levers") or stability_insight.get("top_structural_levers") or [])
    if levers:
        st.markdown('<div class="insight-title">Top 3 Structural Levers</div>', unsafe_allow_html=True)
        for idx, lever in enumerate(levers[:3], start=1):
            title = escape(str(lever.get("title") or f"Lever {idx}"))
            why = escape(str(lever.get("why") or ""))
            action = escape(str(lever.get("action") or ""))
            st.markdown(
                f"""
                <div class="insight-card" style="margin-bottom:0.45rem; padding:0.75rem 0.9rem;">
                  <div class="insight-finding" style="font-size:15px;">{idx}. {title}</div>
                  <div class="insight-support" style="margin-bottom:0.2rem;">{why}</div>
                  <div class="insight-support" style="color:#d6d6ef;">Action: {action}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_chat(chat_key: str, data: dict[str, Any]) -> None:
    _section_label("Ask About Your Data")
    st.markdown('<div class="insight-support">Grounded in precomputed insights only.</div>', unsafe_allow_html=True)

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    pending_key = f"pending_question_{chat_key}"
    processing_key = f"processing_{chat_key}"
    if pending_key not in st.session_state:
        st.session_state[pending_key] = None
    if processing_key not in st.session_state:
        st.session_state[processing_key] = False

    chat_rows = []
    for msg in st.session_state[chat_key]:
        cls = "chat-user" if msg["role"] == "user" else "chat-assistant"
        chat_rows.append(f'<div class="{cls}">{escape(str(msg["content"]))}</div>')
    st.markdown(f'<div class="chat-shell">{"".join(chat_rows)}</div>', unsafe_allow_html=True)

    question = st.chat_input("Ask a question about your insights...")
    if question:
        st.session_state[chat_key].append({"role": "user", "content": question})
        st.session_state[pending_key] = question
        st.session_state[processing_key] = True
        st.rerun()

    pending_question = st.session_state.get(pending_key)
    if pending_question:
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="chat-assistant"><div class="typing"><span></span><span></span><span></span></div></div>',
            unsafe_allow_html=True,
        )

        try:
            answer = generate_narrative(pending_question, data)
        except Exception as exc:
            err = str(exc)
            if "api" in err.lower() or "key" in err.lower() or "OPENAI_API_KEY" in err:
                if os.getenv("OPENROUTER_API_KEY"):
                    answer = "Could not call OpenRouter. Check OPENROUTER_API_KEY and OPENROUTER_MODEL, then retry."
                else:
                    answer = "Could not call OpenAI. Check OPENAI_API_KEY and OPENAI_MODEL, then retry."
            else:
                answer = f"Failed to generate response: {err}"

        st.session_state[chat_key].append({"role": "assistant", "content": answer})
        st.session_state[pending_key] = None
        st.session_state[processing_key] = False
        typing_placeholder.empty()
        st.rerun()


def compute_insights_from_uploads(chatgpt_file: Any, txn_file: Any, cal_file: Any) -> dict[str, Any]:
    # TODO: implement parsers
    return {"persona": "you", "profile_name": "Your Data", "insights": []}


def _render_dashboard(data: dict[str, Any], chat_key: str, orb_fast: bool, behavioral_overlay: bool, macro_overlay: bool) -> None:
    profile_name = data.get("profile_name") or "Your Data"
    _render_header(profile_name, orb_fast=orb_fast)

    stress_insight = _find_insight(data, "stress_spend_correlation")
    theme_insight = _find_insight(data, "top_anxiety_themes")
    goal_insight = _find_insight(data, "months_to_goal")
    rate_insight = _find_insight(data, "invoice_rate_risk")
    resilience_stability = _find_insight(data, "resilience_stability")
    resilience_volatility = _find_insight(data, "resilience_volatility_index")
    resilience_liquidity = _find_insight(data, "resilience_liquidity_runway_forecast")
    resilience_regret = _find_insight(data, "resilience_regret_risk_signal")
    resilience_decomposition = _find_insight(data, "resilience_decomposition")

    _render_kpi_row(stress_insight, goal_insight, theme_insight)
    _section_spacer()

    if stress_insight:
        _section_label("Stress vs Discretionary Spend")
        st.markdown(
            f'<div class="insight-support" style="margin-bottom:0.4rem;">{escape(_one_sentence(stress_insight.get("finding")))}</div>',
            unsafe_allow_html=True,
        )
        spike_weeks = stress_insight.get("spike_weeks") or []
        weekly_series = stress_insight.get("weekly_series") or []
        if spike_weeks:
            _render_spike_chart(spike_weeks, weekly_series)
            _section_spacer()
        _render_spike_details(stress_insight)
        _section_spacer()

    if theme_insight:
        _section_label("Recurring Themes")
        _render_insight_card("Recurring Themes", theme_insight)
        _section_spacer()

    if goal_insight:
        _section_label("Savings Goal Velocity")
        _render_insight_card("Savings Goal", goal_insight)
        _section_spacer()

    if rate_insight:
        _section_label("Freelancer Rate Signal")
        match_count = len(rate_insight.get("matches") or [])
        support = f"Low-rate matches detected: {match_count}. Estimated leakage: ${_fmt_number(rate_insight.get('dollar_impact'), 2)}."
        _render_insight_card("Rate Risk", rate_insight, support_override=support)
        _section_spacer()

    if resilience_stability:
        _section_label("Financial Resilience Model")
        _render_resilience_panel(
            resilience_stability,
            resilience_volatility,
            resilience_liquidity,
            resilience_regret,
            resilience_decomposition,
            behavioral_overlay=behavioral_overlay,
            macro_overlay=macro_overlay,
        )
        _section_spacer()

    _section_label("Data Story")
    _render_data_story(data.get("consent", {}))
    _section_spacer()
    _gradient_divider()
    _section_spacer()
    _render_chat(chat_key, data)


def _render_your_data_placeholder(has_upload: bool, orb_fast: bool) -> None:
    _render_header("Your Data", orb_fast=orb_fast)
    _section_label("Insights Status")
    status = (
        "Files detected. Click Analyze My Data to generate your first insight cards."
        if has_upload
        else "Add at least one export file to unlock analysis."
    )
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">Pipeline</div>
          <div class="insight-finding">Upload -> Parse -> Compute -> Chat</div>
          <div class="insight-support">{escape(status)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="LifeLedger", page_icon="💰", layout="wide")
    _inject_global_style()
    if "entered_app" not in st.session_state:
        st.session_state["entered_app"] = False
    if "landing_view" not in st.session_state:
        st.session_state["landing_view"] = "demo"

    if not st.session_state["entered_app"]:
        _render_welcome_gate()
        return

    _render_orb_overlay()

    st.sidebar.title("💰 LifeLedger")
    st.sidebar.caption("Connect your money to your life.")

    selected = st.sidebar.selectbox(
        "Demo Persona",
        options=list(PERSONA_OPTIONS.keys()),
        format_func=lambda pid: PERSONA_OPTIONS[pid],
    )

    st.sidebar.markdown("---")
    behavioral_overlay = st.sidebar.toggle("Behavioral Overlay", value=True)
    macro_overlay = st.sidebar.toggle("Macro Overlay", value=True)
    st.sidebar.caption("Resilience overlays update adjusted stability and decomposition.")
    st.sidebar.markdown("---")
    st.sidebar.caption("All data is synthetic and processed locally.")

    if st.session_state.get("landing_view") == "your_data":
        tab_your_data, tab_demo = st.tabs(["🔒 Your Data", "📊 Demo"])
    else:
        tab_demo, tab_your_data = st.tabs(["📊 Demo", "🔒 Your Data"])

    with tab_demo:
        data = _load_insights(selected)
        demo_chat_key = f"chat_history_demo_{selected}"
        demo_processing = st.session_state.get(f"processing_{demo_chat_key}", False)
        _render_dashboard(
            data,
            chat_key=demo_chat_key,
            orb_fast=demo_processing,
            behavioral_overlay=behavioral_overlay,
            macro_overlay=macro_overlay,
        )

    with tab_your_data:
        st.markdown('<div class="hero-wrap"><h1 class="hero-title">Analyze Your Own Exported Data</h1></div>', unsafe_allow_html=True)
        st.subheader("Your files never leave this session. Nothing is stored.")

        chatgpt_file = st.file_uploader("ChatGPT or Claude export", type=["json", "zip"], key="upload_chatgpt")
        st.caption("Export from chatgpt.com → Settings → Data Controls → Export")

        txn_file = st.file_uploader("Bank transactions (any CSV)", type=["csv"], key="upload_txn")
        st.caption("Works with Chase, BofA, Amex, Mint, or any bank CSV export")

        cal_file = st.file_uploader("Google Calendar", type=["ics"], key="upload_cal")
        st.caption("Export from calendar.google.com → Settings → Export")

        st.markdown(
            '<div class="consent-banner">🔒 Local processing only. Your raw data is never sent anywhere. '
            "Only anonymized insight summaries are sent to the AI for chat Q&amp;A.</div>",
            unsafe_allow_html=True,
        )

        has_upload = any([chatgpt_file is not None, txn_file is not None, cal_file is not None])
        if "your_data_payload" not in st.session_state:
            st.session_state["your_data_payload"] = None
        if "your_data_analyzing" not in st.session_state:
            st.session_state["your_data_analyzing"] = False

        analyze_clicked = st.button(
            "Analyze My Data",
            use_container_width=True,
            disabled=not has_upload,
            type="primary",
            key="analyze_my_data_btn",
        )

        if analyze_clicked:
            st.session_state["your_data_analyzing"] = True
            st.rerun()

        your_chat_key = "chat_history_your_data"
        your_chat_processing = st.session_state.get(f"processing_{your_chat_key}", False)
        your_orb_fast = bool(st.session_state.get("your_data_analyzing")) or bool(your_chat_processing)
        _render_your_data_placeholder(has_upload=has_upload, orb_fast=your_orb_fast)

        if st.session_state.get("your_data_analyzing"):
            with st.spinner("Reading your data..."):
                st.session_state["your_data_payload"] = compute_insights_from_uploads(chatgpt_file, txn_file, cal_file)
            st.session_state["your_data_analyzing"] = False
            st.rerun()

        your_data_payload = st.session_state.get("your_data_payload")
        if your_data_payload:
            if not your_data_payload.get("insights"):
                st.info("Upload parsing coming soon — ChatGPT parser is next.")
            else:
                your_processing = st.session_state.get(f"processing_{your_chat_key}", False)
                _render_dashboard(
                    your_data_payload,
                    chat_key=your_chat_key,
                    orb_fast=your_processing,
                    behavioral_overlay=behavioral_overlay,
                    macro_overlay=macro_overlay,
                )


if __name__ == "__main__":
    main()
