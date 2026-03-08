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

_SUGGESTED_QUESTIONS = [
    "What drives my spending spikes?",
    "Which subscriptions should I cancel?",
    "What are my biggest anxiety themes?",
    "When do I overspend the most?",
]


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


# ---------------------------------------------------------------------------
# Global Styles — "Warm Noir Editorial"
# ---------------------------------------------------------------------------
def _inject_global_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

        :root {
          --canvas: #0c0c10;
          --surface: #141418;
          --surface-raised: #1c1c22;
          --surface-hover: #22222a;
          --gold: #c9a55c;
          --gold-dim: rgba(201, 165, 92, 0.15);
          --gold-glow: rgba(201, 165, 92, 0.08);
          --emerald: #4ade80;
          --emerald-dim: rgba(74, 222, 128, 0.12);
          --coral: #f87171;
          --coral-dim: rgba(248, 113, 113, 0.12);
          --amber: #f59e0b;
          --text-primary: #e8e4de;
          --text-secondary: #8a8590;
          --text-tertiary: #5a5660;
          --border: rgba(255, 255, 255, 0.06);
          --border-gold: rgba(201, 165, 92, 0.2);
          --font-display: 'DM Serif Display', Georgia, serif;
          --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;
          --radius: 14px;
          --radius-sm: 8px;
          --radius-xs: 6px;
          --shadow-card: 0 2px 20px rgba(0,0,0,0.3), 0 0 0 1px var(--border);
          --shadow-gold: 0 4px 30px rgba(201, 165, 92, 0.06);
          --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
          background: var(--canvas) !important;
          color: var(--text-primary);
          font-family: var(--font-body);
          font-weight: 400;
        }

        /* Grain texture overlay */
        [data-testid="stApp"]::before {
          content: "";
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
          background-repeat: repeat;
          background-size: 256px 256px;
        }

        [data-testid="stMainBlockContainer"], .block-container {
          max-width: 1100px !important;
          margin: 0 auto;
          padding: 0 1.5rem 2rem !important;
          position: relative;
          z-index: 1;
        }

        /* Hide default Streamlit header/footer */
        header[data-testid="stHeader"] { background: transparent !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }

        [data-testid="stSidebar"] {
          background: #0e0e13 !important;
          border-right: 1px solid var(--border) !important;
        }

        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption p {
          font-family: var(--font-body);
          color: var(--text-secondary);
        }

        /* ── Hero ───────────────────────────────────────── */
        .ll-hero {
          padding: 2.5rem 0 1.8rem;
          position: relative;
        }

        .ll-hero-name {
          font-family: var(--font-display);
          font-size: clamp(2.4rem, 5vw, 3.6rem);
          font-weight: 400;
          color: var(--text-primary);
          line-height: 1.08;
          margin: 0;
          letter-spacing: -0.01em;
        }

        .ll-hero-sub {
          margin-top: 0.5rem;
          font-size: 0.95rem;
          color: var(--text-tertiary);
          font-weight: 300;
          letter-spacing: 0.02em;
        }

        .ll-hero-rule {
          margin-top: 1.5rem;
          height: 1px;
          border: 0;
          background: linear-gradient(90deg, var(--gold) 0%, var(--gold-dim) 60%, transparent 100%);
        }

        /* ── Section Labels ─────────────────────────────── */
        .ll-label {
          font-family: var(--font-body);
          text-transform: uppercase;
          letter-spacing: 0.18em;
          font-size: 10px;
          font-weight: 600;
          color: var(--gold);
          margin-bottom: 0.75rem;
          margin-top: 0.25rem;
        }

        /* ── KPI Cards ──────────────────────────────────── */
        .ll-kpi-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
        }

        .ll-kpi {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 1.4rem 1.5rem 1.2rem;
          position: relative;
          overflow: hidden;
          transition: border-color 0.3s var(--ease-out), box-shadow 0.3s var(--ease-out);
        }

        .ll-kpi::before {
          content: "";
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 2px;
          background: var(--kpi-accent, var(--gold));
          opacity: 0;
          transition: opacity 0.3s var(--ease-out);
        }

        .ll-kpi:hover {
          border-color: var(--border-gold);
          box-shadow: var(--shadow-gold);
        }

        .ll-kpi:hover::before { opacity: 1; }

        .ll-kpi-label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: var(--text-tertiary);
          font-weight: 600;
          margin-bottom: 0.75rem;
        }

        .ll-kpi-value {
          font-family: var(--font-display);
          font-size: 2.6rem;
          line-height: 1;
          margin-bottom: 0.6rem;
        }

        .ll-kpi-detail {
          font-size: 12px;
          color: var(--text-secondary);
          line-height: 1.5;
          overflow: hidden;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
        }

        /* ── Insight Cards ──────────────────────────────── */
        .ll-insight {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 1.5rem 1.6rem;
          margin-bottom: 0.85rem;
          transition: border-color 0.3s var(--ease-out);
        }

        .ll-insight:hover {
          border-color: var(--border-gold);
        }

        .ll-insight-eyebrow {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.18em;
          color: var(--gold);
          font-weight: 600;
          margin-bottom: 0.6rem;
        }

        .ll-insight-headline {
          font-family: var(--font-display);
          font-size: 1.25rem;
          color: var(--text-primary);
          line-height: 1.3;
          margin-bottom: 0.5rem;
        }

        .ll-insight-body {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.55;
          margin-bottom: 0.75rem;
        }

        /* ── Pills ──────────────────────────────────────── */
        .ll-pills {
          display: flex;
          gap: 0.4rem;
          flex-wrap: wrap;
        }

        .ll-pill {
          background: var(--gold-dim);
          border: 1px solid var(--border-gold);
          border-radius: 100px;
          padding: 4px 14px;
          font-size: 11px;
          font-weight: 500;
          color: var(--gold);
          display: inline-block;
        }

        /* ── Consent Banner ─────────────────────────────── */
        .ll-consent {
          background: var(--emerald-dim);
          border-left: 2px solid var(--emerald);
          border-radius: var(--radius-sm);
          padding: 0.85rem 1rem;
          color: var(--emerald);
          font-size: 12px;
          margin-top: 0.75rem;
          line-height: 1.5;
          font-weight: 500;
        }

        /* ── Spike Cards ────────────────────────────────── */
        .ll-spike {
          background: var(--surface);
          border: 1px solid var(--coral-dim);
          border-left: 3px solid var(--coral);
          border-radius: var(--radius);
          padding: 1.4rem 1.5rem;
          margin-bottom: 0.85rem;
        }

        .ll-spike-header {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          margin-bottom: 1.2rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid var(--border);
        }

        .ll-spike-week {
          font-family: var(--font-display);
          font-size: 1.15rem;
          color: var(--coral);
        }

        .ll-spike-meta {
          font-size: 12px;
          color: var(--text-tertiary);
          font-weight: 500;
        }

        .ll-spike-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.5rem;
        }

        .ll-spike-col-title {
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.2em;
          color: var(--text-tertiary);
          font-weight: 700;
          margin-bottom: 0.75rem;
        }

        .ll-tx {
          display: flex;
          justify-content: space-between;
          padding: 0.45rem 0;
          border-bottom: 1px solid var(--border);
          font-size: 13px;
        }

        .ll-tx-name { color: var(--text-secondary); }
        .ll-tx-amt { color: var(--coral); font-weight: 600; font-variant-numeric: tabular-nums; }

        .ll-cal-item {
          padding: 0.45rem 0;
          border-bottom: 1px solid var(--border);
          font-size: 13px;
          color: var(--text-secondary);
        }

        /* ── Chat ───────────────────────────────────────── */
        .ll-chat {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 1.2rem;
          margin-top: 0.75rem;
          min-height: 140px;
        }

        .ll-chat-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 2rem 1rem;
          text-align: center;
        }

        .ll-chat-empty-title {
          font-family: var(--font-display);
          font-size: 1.1rem;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .ll-chat-empty-sub {
          font-size: 12px;
          color: var(--text-tertiary);
          max-width: 340px;
          line-height: 1.5;
          margin-bottom: 1rem;
        }

        .ll-chat-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
          justify-content: center;
        }

        .ll-chat-chip {
          background: var(--gold-dim);
          border: 1px solid var(--border-gold);
          border-radius: 100px;
          padding: 6px 14px;
          font-size: 11px;
          font-weight: 500;
          color: var(--gold);
          cursor: default;
        }

        .ll-msg-user {
          margin-left: auto;
          max-width: 75%;
          background: var(--gold-dim);
          border: 1px solid var(--border-gold);
          border-radius: var(--radius) var(--radius) 4px var(--radius);
          padding: 0.7rem 0.9rem;
          color: var(--text-primary);
          margin-bottom: 0.6rem;
          font-size: 13px;
          line-height: 1.45;
        }

        .ll-msg-assistant {
          margin-right: auto;
          max-width: 80%;
          background: var(--surface-raised);
          border-left: 2px solid var(--emerald);
          border-radius: var(--radius-sm);
          padding: 0.7rem 0.9rem;
          color: #d5f5e3;
          margin-bottom: 0.6rem;
          font-size: 13px;
          line-height: 1.55;
          white-space: pre-wrap;
        }

        .ll-typing {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 0.7rem 0.9rem;
        }

        .ll-typing span {
          width: 5px; height: 5px;
          border-radius: 50%;
          background: var(--emerald);
          animation: ll-blink 1.4s infinite;
        }

        .ll-typing span:nth-child(2) { animation-delay: 0.2s; }
        .ll-typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes ll-blink {
          0%, 80%, 100% { opacity: 0.15; transform: scale(0.85); }
          40% { opacity: 1; transform: scale(1); }
        }

        /* ── Overlay Help ───────────────────────────────── */
        .ll-overlay-help {
          font-size: 11px;
          color: var(--text-secondary);
          background: var(--gold-glow);
          border-left: 2px solid var(--gold);
          border-radius: var(--radius-xs);
          padding: 0.6rem 0.85rem;
          margin-bottom: 0.75rem;
          line-height: 1.5;
          font-weight: 500;
        }

        /* ── Upload Zones ───────────────────────────────── */
        .ll-upload {
          background: var(--surface);
          border: 1.5px dashed var(--border-gold);
          border-radius: var(--radius);
          padding: 1rem 1.2rem;
          margin-bottom: 0.5rem;
          transition: background 0.2s, border-color 0.2s;
        }

        .ll-upload:hover {
          background: var(--surface-hover);
          border-color: var(--gold);
        }

        .ll-upload-label {
          font-family: var(--font-display);
          font-size: 0.95rem;
          color: var(--text-primary);
          margin-bottom: 2px;
        }

        .ll-upload-hint {
          font-size: 11px;
          color: var(--text-tertiary);
        }

        /* ── Form Overrides ─────────────────────────────── */
        .stChatInput textarea,
        .stTextInput input {
          background: var(--surface-raised) !important;
          color: var(--text-primary) !important;
          border: 1px solid var(--border) !important;
          border-radius: var(--radius-sm) !important;
          font-family: var(--font-body) !important;
        }

        .stChatInput textarea:focus,
        .stTextInput input:focus {
          border-color: var(--gold) !important;
          box-shadow: 0 0 0 2px var(--gold-dim) !important;
          outline: none !important;
        }

        [data-baseweb="select"] > div {
          background: var(--surface-raised) !important;
          border: 1px solid var(--border) !important;
          color: var(--text-primary) !important;
          border-radius: var(--radius-sm) !important;
          font-family: var(--font-body) !important;
        }

        .stAlert, .stInfo, .stWarning {
          background: var(--surface) !important;
          border: 1px solid var(--border) !important;
          color: var(--text-secondary) !important;
          font-family: var(--font-body) !important;
          border-radius: var(--radius-sm) !important;
        }

        div[data-testid="metric-container"] label,
        div[data-testid="metric-container"] div[data-testid="stMetricLabel"] {
          text-transform: uppercase;
          letter-spacing: 0.14em;
          font-size: 10px;
          font-weight: 600;
          color: var(--text-tertiary) !important;
          font-family: var(--font-body) !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
          font-family: var(--font-display) !important;
          font-size: 2rem;
          color: var(--text-primary) !important;
        }

        .stButton > button {
          min-height: 46px;
          font-family: var(--font-body) !important;
          font-weight: 600;
          border-radius: var(--radius-sm) !important;
          letter-spacing: 0.02em;
        }

        .stButton > button[kind="primary"] {
          background: var(--gold) !important;
          color: #0c0c10 !important;
          border: none !important;
        }

        .stButton > button[kind="primary"]:hover {
          background: #d4b06a !important;
        }

        /* Focus visible */
        button:focus-visible, a:focus-visible, [role="button"]:focus-visible {
          outline: 2px solid var(--gold);
          outline-offset: 2px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
          gap: 0;
          border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
          font-family: var(--font-body) !important;
          font-weight: 600 !important;
          font-size: 13px !important;
          letter-spacing: 0.04em;
          color: var(--text-tertiary) !important;
          padding: 0.6rem 1.2rem !important;
          border-bottom: 2px solid transparent;
        }

        .stTabs [aria-selected="true"] {
          color: var(--gold) !important;
          border-bottom-color: var(--gold) !important;
        }

        /* ── Reduced Motion ─────────────────────────────── */
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }

        /* ── Responsive ─────────────────────────────────── */
        @media (max-width: 920px) {
          .ll-kpi-grid { grid-template-columns: 1fr 1fr; }
          .ll-spike-grid { grid-template-columns: 1fr; }
          .ll-hero-name { font-size: 2rem; }
        }

        @media (max-width: 600px) {
          .ll-kpi-grid { grid-template-columns: 1fr; }
          .ll-msg-user, .ll-msg-assistant { max-width: 100%; }
        }

        /* ── Page Load Animation ────────────────────────── */
        @keyframes ll-fade-up {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .ll-animate {
          animation: ll-fade-up 0.5s var(--ease-out) both;
        }

        .ll-animate-d1 { animation-delay: 0.05s; }
        .ll-animate-d2 { animation-delay: 0.12s; }
        .ll-animate-d3 { animation-delay: 0.19s; }
        .ll-animate-d4 { animation-delay: 0.26s; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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
    st.markdown(f'<div class="ll-label">{escape(name)}</div>', unsafe_allow_html=True)


def _section_spacer() -> None:
    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)


def _divider() -> None:
    st.markdown(
        '<div style="height:1px; background:linear-gradient(90deg, '
        'var(--gold-dim), transparent); margin:12px 0 28px;"></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Welcome Gate
# ---------------------------------------------------------------------------
def _render_welcome_gate() -> bool:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .ll-welcome {
          min-height: 90vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          animation: ll-fade-up 0.6s var(--ease-out) both;
        }
        .ll-welcome-wordmark {
          font-family: var(--font-display);
          font-size: clamp(3rem, 8vw, 6rem);
          color: var(--text-primary);
          line-height: 1;
          margin-bottom: 0.3rem;
          letter-spacing: -0.02em;
        }
        .ll-welcome-wordmark span {
          color: var(--gold);
        }
        .ll-welcome-tagline {
          font-size: 1.05rem;
          color: var(--text-tertiary);
          font-weight: 300;
          letter-spacing: 0.04em;
          margin-bottom: 2.5rem;
          max-width: 400px;
        }
        .ll-welcome-line {
          width: 48px;
          height: 1.5px;
          background: var(--gold);
          margin: 0 auto 2rem;
          opacity: 0.5;
        }
        </style>
        <div class="ll-welcome">
          <div class="ll-welcome-wordmark">Life<span>Ledger</span></div>
          <div class="ll-welcome-line"></div>
          <div class="ll-welcome-tagline">Connect your money to your life with grounded insights.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.5, 1, 1.5])
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


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def _render_header(profile_name: str, orb_fast: bool) -> None:
    st.markdown(
        f"""
        <div class="ll-hero ll-animate">
          <h1 class="ll-hero-name">{escape(profile_name)}</h1>
          <div class="ll-hero-sub">This is what your data reveals.</div>
          <hr class="ll-hero-rule" />
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Orb (refined)
# ---------------------------------------------------------------------------
def _render_orb_overlay() -> None:
    st.markdown(
        """
<style>
.ll-orb-wrap {
  position: fixed;
  top: 56px; right: 32px;
  width: 80px; height: 80px;
  z-index: 999;
  pointer-events: none;
}
.ll-orb {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  width: 36px; height: 36px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #d4b06a, #c9a55c 50%, #8b6914 100%);
  box-shadow: 0 0 24px rgba(201,165,92,0.35), 0 0 60px rgba(201,165,92,0.1);
  animation: ll-breathe 4s ease-in-out infinite;
}
.ll-orb-ring {
  position: absolute;
  top: 50%; left: 50%;
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(201,165,92,0.3);
  transform: translate(-50%,-50%) scale(1);
  animation: ll-pulse 3s ease-out infinite;
}
.ll-orb-ring:nth-child(2) { animation-delay: 0.8s; }
@keyframes ll-pulse {
  0%   { transform: translate(-50%,-50%) scale(1); opacity: 0.5; }
  100% { transform: translate(-50%,-50%) scale(2.5); opacity: 0; }
}
@keyframes ll-breathe {
  0%,100% { transform: translate(-50%,-50%) scale(0.92); }
  50%     { transform: translate(-50%,-50%) scale(1.08); }
}
</style>
<div class="ll-orb-wrap">
  <div class="ll-orb-ring"></div>
  <div class="ll-orb-ring"></div>
  <div class="ll-orb"></div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------
def _render_metric_card(label: str, value: str, detail: str, accent: str) -> str:
    return f"""
    <div class="ll-kpi" style="--kpi-accent: {accent};">
      <div class="ll-kpi-label">{escape(label)}</div>
      <div class="ll-kpi-value" style="color:{accent};">{escape(value)}</div>
      <div class="ll-kpi-detail">{escape(detail)}</div>
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

    cards = "".join([
        _render_metric_card("Stress \u00d7 Spend Correlation", corr_value, corr_detail, "var(--gold)"),
        _render_metric_card("Months to Savings Goal", months_value, months_detail, "var(--emerald)"),
        _render_metric_card("Top Anxiety Themes", themes_value, themes_detail, "var(--coral)"),
    ])
    st.markdown(f'<div class="ll-kpi-grid ll-animate ll-animate-d1">{cards}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Insight Card
# ---------------------------------------------------------------------------
def _render_actions_pills(actions: list[str]) -> str:
    if not actions:
        return ""
    pills = "".join(f'<span class="ll-pill">{escape(a)}</span>' for a in actions)
    return f'<div class="ll-pills">{pills}</div>'


def _render_insight_card(section_title: str, insight: dict[str, Any], support_override: str | None = None) -> None:
    finding = _one_sentence(insight.get("finding"))
    evidence = insight.get("evidence") or []
    support = support_override if support_override is not None else (str(evidence[0]) if evidence else "No supporting detail available.")
    actions = insight.get("recommended_next_actions") or []

    st.markdown(
        f"""
        <div class="ll-insight">
          <div class="ll-insight-eyebrow">{escape(section_title)}</div>
          <div class="ll-insight-headline">{escape(finding)}</div>
          <div class="ll-insight-body">{escape(support)}</div>
          {_render_actions_pills([str(a) for a in actions])}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Data Story
# ---------------------------------------------------------------------------
def _render_data_story(consent: dict[str, Any]) -> None:
    story_summary = (
        "Exported synthetic records across calendar, transactions, conversations, email, and social logs "
        "are fused to compute stress patterns, discretionary spend trends, and cross-source weekly insights."
    )
    story_detail = (
        "Multi-source linkage matters because single-source views miss behavioral links that appear only when "
        "calendar pressure, money movement, and language signals are combined."
    )

    st.markdown(
        f"""
        <div class="ll-insight">
          <div class="ll-insight-eyebrow">Data Story</div>
          <div class="ll-insight-headline">{escape(story_summary)}</div>
          <div class="ll-insight-body">{escape(story_detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dataset = consent.get("dataset_type", "unknown") if consent else "unknown"
    retention = consent.get("retention", "unknown") if consent else "unknown"
    consent_text = (
        f"Local processing only \u2014 synthetic mode. No raw records reach the LLM. "
        f"Dataset: {dataset} \u00b7 Retention: {retention}"
    )
    st.markdown(f'<div class="ll-consent">{escape(consent_text)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Spike helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Spike Chart (Plotly — updated palette)
# ---------------------------------------------------------------------------
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
            x=weeks, y=spend, mode="lines+markers",
            line={"color": "#f87171", "width": 2},
            marker={"size": 5, "color": "#f87171"},
            fill="tozeroy",
            fillcolor="rgba(248,113,113,0.06)",
            name="Discretionary Spend",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=weeks, y=stress_smooth, mode="lines",
            line={"color": "#c9a55c", "width": 2, "dash": "dot"},
            name="Stress Score",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=spike_x, y=spike_y, mode="markers",
            marker={"symbol": "diamond", "size": 12, "color": "#f87171",
                    "line": {"color": "#e8e4de", "width": 1.5}},
            name="Spike Week",
        ),
        secondary_y=False,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,20,24,0.6)",
        font={"family": "Plus Jakarta Sans, system-ui", "color": "#8a8590"},
        height=320,
        margin={"l": 48, "r": 48, "t": 16, "b": 44},
        legend={"orientation": "h", "y": -0.18, "font": {"color": "#8a8590", "size": 11}},
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", tickfont={"color": "#5a5660", "size": 10})
    fig.update_yaxes(
        title_text="Spend ($)", gridcolor="rgba(255,255,255,0.04)",
        tickfont={"color": "#5a5660", "size": 10},
        title_font={"color": "#5a5660", "size": 11},
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Stress", overlaying="y", side="right", range=[0, 1.2],
        gridcolor="rgba(0,0,0,0)",
        tickfont={"color": "#5a5660", "size": 10},
        title_font={"color": "#5a5660", "size": 11},
        secondary_y=True,
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Spike Detail Cards
# ---------------------------------------------------------------------------
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
        tx_rows: list[str] = []
        for tx in txns:
            text = escape(str(tx.get("text", "Transaction")))
            amount = _fmt_number(tx.get("amount"), 2)
            tx_rows.append(f'<div class="ll-tx"><span class="ll-tx-name">{text}</span><span class="ll-tx-amt">${amount}</span></div>')
        if not tx_rows:
            tx_rows.append('<div class="ll-tx"><span class="ll-tx-name" style="color:var(--text-tertiary)">No discretionary transactions matched.</span><span></span></div>')

        events = spike.get("calendar_events") or []
        cal_rows: list[str] = []
        for event in events:
            title = str(event.get("title", "Event"))
            date = str(event.get("date", "N/A"))
            cal_rows.append(f'<div class="ll-cal-item">{escape(date)} \u2014 {escape(title)}</div>')
        if not cal_rows:
            cal_rows.append('<div class="ll-cal-item" style="color:var(--text-tertiary)">No calendar evidence linked.</div>')

        st.markdown(
            f"""
            <div class="ll-spike">
              <div class="ll-spike-header">
                <span class="ll-spike-week">Week {week}</span>
                <span class="ll-spike-meta">${spend} spent &middot; stress {stress}</span>
              </div>
              <div class="ll-spike-grid">
                <div>
                  <div class="ll-spike-col-title">Transactions</div>
                  {"".join(tx_rows)}
                </div>
                <div>
                  <div class="ll-spike-col-title">Calendar Context</div>
                  {"".join(cal_rows)}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Subscription Panel
# ---------------------------------------------------------------------------
def _render_subscription_panel(sub_insight: dict[str, Any]) -> None:
    subs = sub_insight.get("subscriptions") or []
    if not subs:
        _render_insight_card("Subscriptions", sub_insight)
        return

    monthly = sub_insight.get("monthly_total", 0.0)
    yearly = round(monthly * 12, 2)
    col1, col2 = st.columns(2)
    col1.metric("Monthly Subscriptions", f"${_fmt_number(monthly, 2)}")
    col2.metric("Yearly Cost", f"${_fmt_number(yearly, 2)}")

    rows: list[str] = []
    for sub in subs[:8]:
        name = escape(str(sub.get("name", "Unknown")))
        amt = _fmt_number(sub.get("amount"), 2)
        count = sub.get("occurrences", 0)
        rows.append(
            f'<div class="ll-tx">'
            f'<span class="ll-tx-name">{name} <span style="color:var(--text-tertiary);font-size:11px;">({count}x)</span></span>'
            f'<span class="ll-tx-amt">${amt}/mo</span></div>'
        )

    st.markdown(
        f'<div class="ll-insight" style="padding:1.2rem 1.4rem;">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )
    actions = sub_insight.get("recommended_next_actions") or []
    if actions:
        st.markdown(_render_actions_pills([str(a) for a in actions]), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Day of Week Chart
# ---------------------------------------------------------------------------
def _render_dow_chart(dow_insight: dict[str, Any]) -> None:
    by_day = dow_insight.get("by_day") or {}
    if not by_day:
        _render_insight_card("Day of Week", dow_insight)
        return

    expensive = dow_insight.get("expensive_day")
    days = list(by_day.keys())
    values = list(by_day.values())
    colors = ["#c9a55c" if d == expensive else "rgba(201,165,92,0.3)" for d in days]

    fig = go.Figure(
        go.Bar(
            x=days, y=values,
            marker_color=colors,
            text=[f"${v:.0f}" for v in values],
            textposition="outside",
            textfont={"family": "Plus Jakarta Sans", "size": 11, "color": "#8a8590"},
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,20,24,0.6)",
        font={"family": "Plus Jakarta Sans, system-ui", "color": "#8a8590"},
        height=280,
        margin={"l": 40, "r": 20, "t": 10, "b": 40},
        yaxis_title="Avg Spend ($)",
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)", tickfont={"color": "#8a8590", "size": 11})
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", tickfont={"color": "#5a5660", "size": 10})
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Worry Timeline Chart
# ---------------------------------------------------------------------------
def _render_worry_chart(worry_insight: dict[str, Any]) -> None:
    timeline = worry_insight.get("timeline") or []
    if not timeline:
        return

    weeks = [r["year_week"] for r in timeline]
    mentions = [r["worry_mentions"] for r in timeline]
    spend = [r.get("discretionary_spend", 0.0) for r in timeline]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=weeks, y=mentions,
            marker_color="rgba(248,113,113,0.6)",
            name="Worry Mentions",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=weeks, y=spend, mode="lines+markers",
            line={"color": "#c9a55c", "width": 2},
            marker={"size": 4, "color": "#c9a55c"},
            name="Discretionary Spend",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,20,24,0.6)",
        font={"family": "Plus Jakarta Sans, system-ui", "color": "#8a8590"},
        height=300,
        margin={"l": 48, "r": 48, "t": 16, "b": 44},
        legend={"orientation": "h", "y": -0.18, "font": {"color": "#8a8590", "size": 11}},
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", tickfont={"color": "#5a5660", "size": 10})
    fig.update_yaxes(
        title_text="Worry Mentions", gridcolor="rgba(255,255,255,0.04)",
        tickfont={"color": "#5a5660", "size": 10},
        title_font={"color": "#5a5660", "size": 11},
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Spend ($)", overlaying="y", side="right",
        gridcolor="rgba(0,0,0,0)",
        tickfont={"color": "#5a5660", "size": 10},
        title_font={"color": "#5a5660", "size": 11},
        secondary_y=True,
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def _render_chat(chat_key: str, data: dict[str, Any]) -> None:
    _section_label("Ask About Your Data")

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
        cls = "ll-msg-user" if msg["role"] == "user" else "ll-msg-assistant"
        chat_rows.append(f'<div class="{cls}">{escape(str(msg["content"]))}</div>')

    if not chat_rows:
        chips = "".join(f'<span class="ll-chat-chip">{escape(q)}</span>' for q in _SUGGESTED_QUESTIONS)
        empty = (
            '<div class="ll-chat-empty">'
            '<div class="ll-chat-empty-title">Ask anything about your insights</div>'
            '<div class="ll-chat-empty-sub">'
            'Responses are grounded in your precomputed data. No raw records leave this session.'
            '</div>'
            f'<div class="ll-chat-chips">{chips}</div>'
            '</div>'
        )
        st.markdown(f'<div class="ll-chat">{empty}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ll-chat">{"".join(chat_rows)}</div>', unsafe_allow_html=True)

    question = st.chat_input("Ask a question about your insights\u2026")
    if question:
        st.session_state[chat_key].append({"role": "user", "content": question})
        st.session_state[pending_key] = question
        st.session_state[processing_key] = True
        st.rerun()

    pending_question = st.session_state.get(pending_key)
    if pending_question:
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="ll-msg-assistant"><div class="ll-typing"><span></span><span></span><span></span></div></div>',
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


# ---------------------------------------------------------------------------
# Upload stub
# ---------------------------------------------------------------------------
def compute_insights_from_uploads(chatgpt_file: Any, txn_file: Any, cal_file: Any) -> dict[str, Any]:
    # TODO: implement parsers
    return {"persona": "you", "profile_name": "Your Data", "insights": []}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def _render_dashboard(data: dict[str, Any], chat_key: str, orb_fast: bool, **_kwargs: Any) -> None:
    profile_name = data.get("profile_name") or "Your Data"
    _render_header(profile_name, orb_fast=orb_fast)

    stress_insight = _find_insight(data, "stress_spend_correlation")
    theme_insight = _find_insight(data, "top_anxiety_themes")
    goal_insight = _find_insight(data, "months_to_goal")
    rate_insight = _find_insight(data, "invoice_rate_risk")
    sub_insight = _find_insight(data, "subscription_creep")
    dow_insight = _find_insight(data, "expensive_day_of_week")
    surge_insight = _find_insight(data, "post_payday_surge")
    worry_insight = _find_insight(data, "worry_timeline")

    _render_kpi_row(stress_insight, goal_insight, theme_insight)
    _section_spacer()

    if stress_insight:
        _section_label("Stress vs Discretionary Spend")
        st.markdown(
            f'<div class="ll-insight-body" style="margin-bottom:0.6rem;">{escape(_one_sentence(stress_insight.get("finding")))}</div>',
            unsafe_allow_html=True,
        )
        spike_weeks = stress_insight.get("spike_weeks") or []
        weekly_series = stress_insight.get("weekly_series") or []
        if spike_weeks:
            _render_spike_chart(spike_weeks, weekly_series)
            _section_spacer()
        _render_spike_details(stress_insight)
        _section_spacer()

    if worry_insight and worry_insight.get("total_worry_mentions", 0) > 0:
        _section_label("Worry Timeline — AI Conversations x Spending")
        _render_insight_card("Cross-Source Insight", worry_insight)
        _render_worry_chart(worry_insight)
        _section_spacer()

    if sub_insight:
        _section_label("Subscription Audit")
        _render_subscription_panel(sub_insight)
        _section_spacer()

    if dow_insight and dow_insight.get("expensive_day"):
        _section_label("Your Spending by Day of Week")
        _render_insight_card("Day of Week", dow_insight)
        _render_dow_chart(dow_insight)
        _section_spacer()

    if surge_insight:
        _section_label("Post-Payday Pattern")
        _render_insight_card("Payday Surge", surge_insight)
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

    _section_label("Data Story")
    _render_data_story(data.get("consent", {}))
    _section_spacer()
    _divider()
    _render_chat(chat_key, data)


# ---------------------------------------------------------------------------
# Your Data Placeholder
# ---------------------------------------------------------------------------
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
        <div class="ll-insight">
          <div class="ll-insight-eyebrow">Pipeline</div>
          <div class="ll-insight-headline">Upload &rarr; Parse &rarr; Compute &rarr; Chat</div>
          <div class="ll-insight-body">{escape(status)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="LifeLedger", page_icon="\U0001f4b0", layout="wide")
    _inject_global_style()
    if "entered_app" not in st.session_state:
        st.session_state["entered_app"] = False
    if "landing_view" not in st.session_state:
        st.session_state["landing_view"] = "demo"

    if not st.session_state["entered_app"]:
        _render_welcome_gate()
        return

    _render_orb_overlay()

    st.sidebar.markdown(
        '<div style="font-family: DM Serif Display, Georgia, serif; font-size: 1.5rem; '
        'color: var(--text-primary, #e8e4de); margin-bottom: 0.15rem;">Life<span style="color:#c9a55c;">Ledger</span></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Connect your money to your life.")

    selected = st.sidebar.selectbox(
        "Demo Persona",
        options=list(PERSONA_OPTIONS.keys()),
        format_func=lambda pid: PERSONA_OPTIONS[pid],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("All data is synthetic and processed locally.")

    if st.session_state.get("landing_view") == "your_data":
        tab_your_data, tab_demo = st.tabs(["Your Data", "Demo"])
    else:
        tab_demo, tab_your_data = st.tabs(["Demo", "Your Data"])

    with tab_demo:
        data = _load_insights(selected)
        demo_chat_key = f"chat_history_demo_{selected}"
        demo_processing = st.session_state.get(f"processing_{demo_chat_key}", False)
        _render_dashboard(data, chat_key=demo_chat_key, orb_fast=demo_processing)

    with tab_your_data:
        st.markdown(
            '<div class="ll-hero ll-animate">'
            '<h1 class="ll-hero-name">Analyze Your Own Data</h1>'
            '<div class="ll-hero-sub">Your files never leave this session. Nothing is stored.</div>'
            '<hr class="ll-hero-rule" />'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ll-upload"><div class="ll-upload-label">Conversations</div>'
            '<div class="ll-upload-hint">ChatGPT or Claude export &mdash; .json or .zip</div></div>',
            unsafe_allow_html=True,
        )
        chatgpt_file = st.file_uploader("ChatGPT or Claude export", type=["json", "zip"], key="upload_chatgpt", label_visibility="collapsed")

        st.markdown(
            '<div class="ll-upload"><div class="ll-upload-label">Bank Transactions</div>'
            '<div class="ll-upload-hint">Any bank CSV &mdash; Chase, BofA, Amex, Mint, etc.</div></div>',
            unsafe_allow_html=True,
        )
        txn_file = st.file_uploader("Bank transactions (any CSV)", type=["csv"], key="upload_txn", label_visibility="collapsed")

        st.markdown(
            '<div class="ll-upload"><div class="ll-upload-label">Calendar</div>'
            '<div class="ll-upload-hint">Google Calendar .ics export</div></div>',
            unsafe_allow_html=True,
        )
        cal_file = st.file_uploader("Google Calendar", type=["ics"], key="upload_cal", label_visibility="collapsed")

        st.markdown(
            '<div class="ll-consent">'
            'Local processing only. Your raw data is never sent anywhere. '
            'Only anonymized insight summaries are sent to the AI for chat Q&amp;A.</div>',
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
            with st.spinner("Reading your data\u2026"):
                st.session_state["your_data_payload"] = compute_insights_from_uploads(chatgpt_file, txn_file, cal_file)
            st.session_state["your_data_analyzing"] = False
            st.rerun()

        your_data_payload = st.session_state.get("your_data_payload")
        if your_data_payload:
            if not your_data_payload.get("insights"):
                st.info("Upload parsing coming soon \u2014 ChatGPT parser is next.")
            else:
                your_processing = st.session_state.get(f"processing_{your_chat_key}", False)
                _render_dashboard(your_data_payload, chat_key=your_chat_key, orb_fast=your_processing)


if __name__ == "__main__":
    main()
