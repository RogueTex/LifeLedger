"""Comprehensive test suite for LifeLedger feature modules.

Tests cover:
  - stress_scorer.compute_stress
  - spend_tagger.tag_spend
  - correlation.compute_correlation
  - insight_engine._validate_insight_schema
  - insight_engine._compute_anxiety_themes
  - upload_parser (CSV, ICS, ChatGPT export)
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project src package is importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.features.stress_scorer import compute_stress, DEADLINE_KEYWORDS
from src.features.spend_tagger import tag_spend, KEYWORD_MAP
from src.features.correlation import compute_correlation
from src.insights.extraction import extract_invoice_facts, extract_worry_facts
from src.insights.insight_engine import (
    _validate_insight_schema,
    _compute_anxiety_themes,
    compute_insights,
    compute_insights_from_dataframes,
)
from src.loaders.persona_loader import build_timeline, load_persona
from src.loaders.upload_parser import parse_transactions_csv, parse_calendar_ics, parse_chatgpt_export


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_calendar_df(events: list[dict]) -> pd.DataFrame:
    """Build a minimal calendar DataFrame from a list of dicts."""
    return pd.DataFrame(events)


def _make_transactions_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _dates(start: str, n: int) -> list[str]:
    """Generate n consecutive date strings starting from *start* (YYYY-MM-DD)."""
    base = datetime.date.fromisoformat(start)
    return [(base + datetime.timedelta(days=i)).isoformat() for i in range(n)]


# ===================================================================
# 1. Stress scorer
# ===================================================================

class TestComputeStress:
    def test_empty_dataframe_returns_empty(self):
        result = compute_stress(pd.DataFrame())
        assert list(result.columns) == ["date", "stress_raw", "stress_smooth"]
        assert len(result) == 0

    def test_none_input_returns_empty(self):
        result = compute_stress(None)
        assert list(result.columns) == ["date", "stress_raw", "stress_smooth"]
        assert len(result) == 0

    def test_single_event(self):
        df = _make_calendar_df([
            {"start": "2025-06-01T09:00:00Z", "title": "Team standup"},
        ])
        result = compute_stress(df)
        assert len(result) == 1
        assert "date" in result.columns
        assert "stress_raw" in result.columns
        assert "stress_smooth" in result.columns

    def test_multiple_events_multiple_days(self):
        events = []
        for d in _dates("2025-06-01", 5):
            for hour in (9, 10, 14):
                events.append({"start": f"{d}T{hour:02d}:00:00Z", "title": "Meeting"})
        result = compute_stress(_make_calendar_df(events))
        assert len(result) == 5
        # stress_raw should be between 0 and 1 (normalised)
        assert result["stress_raw"].min() >= 0.0
        assert result["stress_raw"].max() <= 1.0

    def test_deadline_keyword_increases_stress(self):
        """A day containing a deadline keyword should score higher stress_raw
        than an identical day without one (all else equal)."""
        base_events = [
            {"start": "2025-06-01T09:00:00Z", "title": "Regular standup"},
            {"start": "2025-06-01T10:00:00Z", "title": "Sync call"},
        ]
        deadline_events = [
            {"start": "2025-06-02T09:00:00Z", "title": "OKR deadline review"},
            {"start": "2025-06-02T10:00:00Z", "title": "Sprint demo"},
        ]
        result = compute_stress(_make_calendar_df(base_events + deadline_events))
        day1 = result.loc[result["date"].astype(str) == "2025-06-01", "stress_raw"].iloc[0]
        day2 = result.loc[result["date"].astype(str) == "2025-06-02", "stress_raw"].iloc[0]
        # Day 2 has deadline keywords ("deadline", "review", "demo") so should be higher.
        assert day2 > day1

    def test_smoothing_produces_rolling_average(self):
        """stress_smooth should differ from stress_raw when there are enough
        data points, because it applies a 7-day rolling mean."""
        events = []
        dates = _dates("2025-06-01", 14)
        for i, d in enumerate(dates):
            # Vary meeting count: odd days get 1 meeting, even days get 5
            n_meetings = 5 if i % 2 == 0 else 1
            for j in range(n_meetings):
                events.append({"start": f"{d}T{9 + j:02d}:00:00Z", "title": "Meeting"})
        result = compute_stress(_make_calendar_df(events))
        # After 7+ days the rolling mean should smooth out spikes
        assert len(result) == 14
        diffs = (result["stress_raw"] - result["stress_smooth"]).abs()
        assert diffs.sum() > 0, "Smoothed values should differ from raw"


# ===================================================================
# 2. Spend tagger
# ===================================================================

class TestTagSpend:
    def test_empty_input(self):
        tagged, weekly = tag_spend(pd.DataFrame())
        assert "is_discretionary" in tagged.columns
        assert "year_week" in weekly.columns
        assert len(tagged) == 0

    def test_none_input(self):
        tagged, weekly = tag_spend(None)
        assert len(tagged) == 0
        assert len(weekly) == 0

    def test_starbucks_tagged_as_coffee(self):
        df = _make_transactions_df([
            {"date": "2025-06-01", "merchant": "Starbucks #1234", "amount": 5.75},
        ])
        tagged, _ = tag_spend(df)
        assert bool(tagged.iloc[0]["is_discretionary"]) is True
        assert "coffee" in tagged.iloc[0]["spend_tags"]

    def test_uber_eats_tagged_as_food_delivery(self):
        df = _make_transactions_df([
            {"date": "2025-06-01", "merchant": "UBER EATS order", "amount": 22.00},
        ])
        tagged, _ = tag_spend(df)
        assert bool(tagged.iloc[0]["is_discretionary"]) is True
        assert "food_delivery" in tagged.iloc[0]["spend_tags"]

    def test_amazon_tagged_as_shopping(self):
        df = _make_transactions_df([
            {"date": "2025-06-02", "merchant": "Amazon.com purchase", "amount": 49.99},
        ])
        tagged, _ = tag_spend(df)
        assert bool(tagged.iloc[0]["is_discretionary"]) is True
        assert "shopping" in tagged.iloc[0]["spend_tags"]

    def test_non_discretionary_not_tagged(self):
        df = _make_transactions_df([
            {"date": "2025-06-01", "merchant": "City Water Utility", "amount": 45.00},
        ])
        tagged, _ = tag_spend(df)
        assert bool(tagged.iloc[0]["is_discretionary"]) is False
        assert tagged.iloc[0]["spend_tags"] == []

    def test_weekly_aggregation(self):
        # Two transactions in the same ISO week
        df = _make_transactions_df([
            {"date": "2025-06-02", "merchant": "Starbucks", "amount": 5.00},
            {"date": "2025-06-03", "merchant": "Amazon", "amount": 30.00},
        ])
        _, weekly = tag_spend(df)
        assert len(weekly) == 1
        assert weekly.iloc[0]["weekly_discretionary_total"] == 35.00

    def test_year_week_computation(self):
        df = _make_transactions_df([
            {"date": "2025-01-06", "merchant": "Starbucks", "amount": 5.00},
        ])
        tagged, weekly = tag_spend(df)
        assert tagged.iloc[0]["year_week"] == "2025-02"
        assert weekly.iloc[0]["year_week"] == "2025-02"


# ===================================================================
# 3. Correlation
# ===================================================================

class TestComputeCorrelation:
    def test_empty_inputs_return_gracefully(self):
        result = compute_correlation(
            stress_df=pd.DataFrame(),
            weekly_spend_df=pd.DataFrame(),
            transactions_df=pd.DataFrame(),
            calendar_df=pd.DataFrame(),
        )
        assert result["correlation_coefficient"] is None
        assert result["spike_weeks"] == []
        assert "insufficient" in result["interpretation"].lower() or result["insufficient_variance"] is True

    def test_sufficient_data_produces_correlation(self):
        """Build enough synthetic weeks so Pearson correlation can be computed."""
        # 8 weeks of stress data
        dates_list = _dates("2025-01-06", 56)  # 8 weeks
        stress_rows = []
        for d in dates_list:
            iso = datetime.date.fromisoformat(d).isocalendar()
            week_num = iso.week
            # Stress rises linearly with week number
            raw = (week_num - 1) / 10.0
            stress_rows.append({"date": d, "stress_raw": raw, "stress_smooth": raw})
        stress_df = pd.DataFrame(stress_rows)

        # Weekly spend that correlates with stress
        weekly_spend_rows = []
        for w in range(2, 10):
            yw = f"2025-{w:02d}"
            weekly_spend_rows.append({
                "year_week": yw,
                "weekly_discretionary_total": 50.0 + (w - 2) * 15.0,
            })
        weekly_spend_df = pd.DataFrame(weekly_spend_rows)

        # Minimal transactions and calendar (not strictly needed for correlation coefficient)
        transactions_df = pd.DataFrame(columns=["year_week", "amount", "is_discretionary"])
        calendar_df = pd.DataFrame(columns=["year_week", "text"])

        result = compute_correlation(stress_df, weekly_spend_df, transactions_df, calendar_df)
        assert result["correlation_coefficient"] is not None
        # With linearly correlated data the coefficient should be positive and strong
        assert result["correlation_coefficient"] > 0.5

    def test_spike_weeks_key_present(self):
        result = compute_correlation(
            stress_df=pd.DataFrame(columns=["date", "stress_raw", "stress_smooth"]),
            weekly_spend_df=pd.DataFrame(columns=["year_week", "weekly_discretionary_total"]),
            transactions_df=pd.DataFrame(),
            calendar_df=pd.DataFrame(),
        )
        assert "spike_weeks" in result


# ===================================================================
# 4. Insight schema validation
# ===================================================================

class TestValidateInsightSchema:
    def test_missing_insights_key_raises(self):
        with pytest.raises(ValueError, match="insights"):
            _validate_insight_schema({})

    def test_insights_not_list_raises(self):
        with pytest.raises(ValueError, match="insights"):
            _validate_insight_schema({"insights": "not a list"})

    def test_missing_required_field_raises(self):
        bad_insight = {
            "id": "test_1",
            "title": "Test",
            # missing "finding", "evidence", "dollar_impact"
        }
        with pytest.raises(ValueError, match="missing required field"):
            _validate_insight_schema({"insights": [bad_insight]})

    def test_duplicate_id_raises(self):
        insight = {
            "id": "dup",
            "title": "T",
            "finding": "F",
            "evidence": ["e"],
            "dollar_impact": None,
        }
        with pytest.raises(ValueError, match="Duplicate"):
            _validate_insight_schema({"insights": [insight, insight]})

    def test_valid_payload_passes(self):
        payload = {
            "insights": [
                {
                    "id": "a",
                    "title": "Title A",
                    "finding": "Finding A",
                    "evidence": ["ev1"],
                    "dollar_impact": 100.0,
                },
                {
                    "id": "b",
                    "title": "Title B",
                    "finding": "Finding B",
                    "evidence": [],
                    "dollar_impact": None,
                },
            ]
        }
        # Should not raise
        _validate_insight_schema(payload)


# ===================================================================
# 5. Anxiety themes
# ===================================================================

class TestComputeAnxietyThemes:
    def test_empty_conversations_returns_empty(self):
        assert _compute_anxiety_themes(pd.DataFrame()) == []

    def test_none_input_returns_empty(self):
        assert _compute_anxiety_themes(None) == []

    def test_lexicon_matching_via_text(self):
        df = pd.DataFrame([
            {"text": "I feel so anxious about the promotion timeline", "tags": []},
            {"text": "budget is tight and debt is growing", "tags": []},
        ])
        themes = _compute_anxiety_themes(df)
        theme_names = {t["theme"] for t in themes}
        assert "anxiety" in theme_names
        assert "career" in theme_names
        assert "debt" in theme_names
        assert "money" in theme_names

    def test_tag_matching(self):
        df = pd.DataFrame([
            {"text": "", "tags": ["stress", "burnout"]},
        ])
        themes = _compute_anxiety_themes(df)
        theme_names = {t["theme"] for t in themes}
        assert "stress" in theme_names
        assert "burnout" in theme_names


# ===================================================================
# 6. Upload parsers
# ===================================================================

class TestParseTransactionsCsv:
    def test_basic_csv(self):
        data = b"Date,Description,Amount\n01/15/2025,Starbucks,-5.50\n01/16/2025,Paycheck,2500.00\n"
        df = parse_transactions_csv(data)
        assert len(df) == 2
        assert "ts" in df.columns
        assert "amount" in df.columns
        assert "signed_amount" in df.columns
        assert "year_week" in df.columns
        assert df.iloc[0]["text"] == "Starbucks"
        assert df.iloc[0]["amount"] == 5.50
        assert df.iloc[0]["signed_amount"] == -5.50
        assert df.iloc[1]["signed_amount"] == 2500.00

    def test_alternate_column_names(self):
        data = b"Transaction Date,Transaction Amount,Merchant\n2025-01-15,-42.99,Amazon\n"
        df = parse_transactions_csv(data)
        assert len(df) == 1
        assert df.iloc[0]["amount"] == 42.99
        assert df.iloc[0]["text"] == "Amazon"

    def test_category_becomes_tag(self):
        data = b"Date,Amount,Description,Category\n01/15/2025,-10.00,Coffee Shop,Dining\n"
        df = parse_transactions_csv(data)
        assert len(df) == 1
        assert "dining" in df.iloc[0]["tags"]

    def test_empty_csv_returns_empty(self):
        df = parse_transactions_csv(b"")
        assert len(df) == 0

    def test_malformed_rows_skipped(self):
        data = b"Date,Amount,Description\n01/15/2025,-5.00,Coffee\nnot-a-date,xyz,Bad\n01/16/2025,-10.00,Lunch\n"
        df = parse_transactions_csv(data)
        assert len(df) == 2

    def test_iso_date_format(self):
        data = b"Date,Amount,Description\n2025-03-01,-25.00,Target\n"
        df = parse_transactions_csv(data)
        assert len(df) == 1


class TestParseCalendarIcs:
    def test_basic_ics(self):
        data = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20250115T090000Z
SUMMARY:Team standup
DESCRIPTION:Daily sync
END:VEVENT
END:VCALENDAR"""
        df = parse_calendar_ics(data)
        assert len(df) == 1
        assert "Team standup Daily sync" == df.iloc[0]["text"]
        assert "year_week" in df.columns

    def test_multiple_events(self):
        data = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20250115T090000Z
SUMMARY:Meeting A
END:VEVENT
BEGIN:VEVENT
DTSTART:20250116T140000Z
SUMMARY:Meeting B
END:VEVENT
BEGIN:VEVENT
DTSTART:20250117T100000Z
SUMMARY:Meeting C
END:VEVENT
END:VCALENDAR"""
        df = parse_calendar_ics(data)
        assert len(df) == 3

    def test_date_only_format(self):
        data = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250120
SUMMARY:All day event
END:VEVENT
END:VCALENDAR"""
        df = parse_calendar_ics(data)
        assert len(df) == 1

    def test_empty_ics_returns_empty(self):
        df = parse_calendar_ics(b"BEGIN:VCALENDAR\nEND:VCALENDAR")
        assert len(df) == 0

    def test_malformed_ics_returns_empty(self):
        df = parse_calendar_ics(b"this is not an ics file")
        assert len(df) == 0


class TestParseChatgptExport:
    def test_basic_json(self):
        import json as _json
        data = _json.dumps([{
            "title": "Budget help",
            "create_time": 1705300000,
            "mapping": {
                "a": {"message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["I am stressed about money"]},
                    "create_time": 1705300000,
                }},
                "b": {"message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Here are tips"]},
                    "create_time": 1705300010,
                }},
            },
        }]).encode()
        df = parse_chatgpt_export(data, "conversations.json")
        assert len(df) == 1  # only user messages
        assert "stressed" in df.iloc[0]["text"]
        assert "stress" in df.iloc[0]["tags"]
        assert "money" in df.iloc[0]["tags"]

    def test_tag_inference(self):
        import json as _json
        data = _json.dumps([{
            "title": "Career anxiety",
            "create_time": 1705300000,
            "mapping": {
                "a": {"message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["anxious about my promotion and nervous about the hiring loop"]},
                    "create_time": 1705300000,
                }},
            },
        }]).encode()
        df = parse_chatgpt_export(data, "export.json")
        tags = df.iloc[0]["tags"]
        assert "anxiety" in tags
        assert "career" in tags

    def test_empty_json_returns_empty(self):
        df = parse_chatgpt_export(b"[]", "conversations.json")
        assert len(df) == 0

    def test_malformed_json_returns_empty(self):
        df = parse_chatgpt_export(b"not json at all", "conversations.json")
        assert len(df) == 0

    def test_zip_with_conversations(self):
        import json as _json
        import io
        import zipfile
        conv_data = _json.dumps([{
            "title": "Test",
            "create_time": 1705300000,
            "mapping": {
                "a": {"message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello world"]},
                    "create_time": 1705300000,
                }},
            },
        }]).encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("conversations.json", conv_data)
        df = parse_chatgpt_export(buf.getvalue(), "export.zip")
        assert len(df) == 1
        assert "Hello world" == df.iloc[0]["text"]

    def test_claude_zip_with_chat_messages(self):
        import json as _json
        import io
        import zipfile

        conv_data = _json.dumps([{
            "name": "Savings stress",
            "created_at": "2026-01-15T09:00:00Z",
            "chat_messages": [
                {
                    "sender": "human",
                    "created_at": "2026-01-15T09:01:00Z",
                    "text": "I am worried about rent and debt this month",
                    "content": [{"type": "text", "text": "I am worried about rent and debt this month"}],
                },
                {
                    "sender": "assistant",
                    "created_at": "2026-01-15T09:02:00Z",
                    "text": "Let's make a plan.",
                    "content": [{"type": "text", "text": "Let's make a plan."}],
                },
            ],
        }]).encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("conversations.json", conv_data)

        df = parse_chatgpt_export(buf.getvalue(), "claude_export.zip")

        assert len(df) == 1
        assert df.iloc[0]["source"] == "ai_chat"
        assert df.iloc[0]["ts"].isoformat() == "2026-01-15T09:01:00+00:00"
        assert "worried" in df.iloc[0]["text"]
        assert "money" in df.iloc[0]["tags"]


class TestUploadProcessor:
    def _run_process_upload(self, payload: dict) -> tuple[int, dict]:
        import json as _json
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "process_upload.py")],
            input=_json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=_PROJECT_ROOT,
            check=False,
        )
        return proc.returncode, _json.loads(proc.stdout)

    def test_rejects_unknown_file_type(self):
        code, body = self._run_process_upload({
            "files": [{"name": "notes.txt", "type": "notes", "data": "SGVsbG8="}],
        })
        assert code == 1
        assert body["error_code"] == "unsupported_file_type"

    def test_rejects_invalid_base64(self):
        code, body = self._run_process_upload({
            "files": [{"name": "bad.csv", "type": "transactions", "data": "not base64!?"}],
        })
        assert code == 1
        assert body["error_code"] == "invalid_file_encoding"


# ===================================================================
# 7. Shipped demo assets
# ===================================================================

class TestDemoAssets:
    EXPECTED_PERSONAS = {
        "p01": "Jordan Lee",
        "p03": "Sasha Moreno",
        "p05": "Theo Nakamura",
    }

    def test_frozen_demo_insights_are_committed_and_schema_valid(self):
        for persona_id, expected_name in self.EXPECTED_PERSONAS.items():
            path = _PROJECT_ROOT / "outputs" / f"insights_{persona_id}.json"
            assert path.exists(), f"Missing frozen demo cache: {path}"

            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            assert payload["schema_version"] == "v1_locked"
            assert payload["persona"] == persona_id
            assert payload["profile_name"] == expected_name
            assert payload["consent"]["dataset_type"] == "synthetic"
            assert len(payload["insights"]) >= 3
            _validate_insight_schema(payload)


# ===================================================================
# 8. Committed raw sample data
# ===================================================================

class TestSamplePersonaData:
    SAMPLE_ROOT = _PROJECT_ROOT / "data" / "sample"
    EXPECTED_PERSONAS = ("p01", "p03", "p05")

    def test_sample_personas_load_and_normalize(self):
        for persona_id in self.EXPECTED_PERSONAS:
            data = load_persona(persona_id, data_root=self.SAMPLE_ROOT)
            assert data["consent"]["dataset_type"] == "synthetic"
            assert len(data["transactions"]) >= 70
            assert len(data["calendar"]) >= 40
            assert len(data["conversations"]) >= 10

            timeline = build_timeline(data)
            assert len(timeline) >= 150
            assert {"bank", "calendar", "ai_chat", "email"}.issubset(set(timeline["source"]))
            assert timeline["year_week"].dropna().str.match(r"^\d{4}-\d{2}$").all()

    def test_sample_persona_can_compute_insights(self, monkeypatch):
        monkeypatch.setenv("LIFELEDGER_PERSONA_DATA_DIR", str(self.SAMPLE_ROOT))
        result = compute_insights("p05")
        _validate_insight_schema(result)
        insight_ids = {insight["id"] for insight in result["insights"]}
        assert "stress_spend_correlation" in insight_ids
        assert "worry_timeline" in insight_ids
        assert "invoice_rate_risk" in insight_ids

    def test_structured_invoice_extraction_from_sample_emails(self):
        data = load_persona("p05", data_root=self.SAMPLE_ROOT)
        facts = extract_invoice_facts(data["emails"])

        assert len(facts) == 4
        for fact in facts:
            assert fact["type"] == "invoice_payment"
            assert fact["source"] == "email"
            assert fact["source_id"].startswith("e_")
            assert fact["amounts"] == [750.0]
            assert fact["hours"] == [15.0]
            assert fact["confidence"] >= 0.9
            assert "$750" in fact["evidence_span"]

    def test_sample_golden_insights_have_confidence_and_provenance(self, monkeypatch):
        monkeypatch.setenv("LIFELEDGER_PERSONA_DATA_DIR", str(self.SAMPLE_ROOT))

        theo = compute_insights("p05")
        _validate_insight_schema(theo)
        assert all(isinstance(insight.get("confidence"), dict) for insight in theo["insights"])
        assert all(isinstance(insight.get("provenance"), dict) for insight in theo["insights"])

        rate = next(insight for insight in theo["insights"] if insight["id"] == "invoice_rate_risk")
        assert rate["flagged"] is True
        assert rate["dollar_impact"] == 900.0
        assert rate["structured_facts_count"] == 4
        assert rate["confidence"]["level"] == "high"
        assert {"email", "calendar"}.issubset(set(rate["provenance"]["source_types"]))
        assert all(match["source_id"].startswith("e_") for match in rate["matches"])
        assert all(match["confidence"] >= 0.9 for match in rate["matches"])

        sasha = compute_insights("p03")
        stress = next(insight for insight in sasha["insights"] if insight["id"] == "stress_spend_correlation")
        surge = next(insight for insight in sasha["insights"] if insight["id"] == "post_payday_surge")
        worry = next(insight for insight in sasha["insights"] if insight["id"] == "worry_timeline")

        assert stress["correlation_coefficient"] > 0.5
        assert stress["confidence"]["level"] == "high"
        assert surge["detected"] is True
        assert surge["payday_count"] > 0
        assert surge["post_payday_total"] > 0
        assert surge["total_spend"] > surge["post_payday_total"]
        assert worry["total_worry_mentions"] > 0
        assert worry["structured_facts_count"] == len(extract_worry_facts(load_persona("p03", data_root=self.SAMPLE_ROOT)["conversations"]))

    def test_subscription_creep_ignores_rent_and_groceries(self, monkeypatch):
        monkeypatch.setenv("LIFELEDGER_PERSONA_DATA_DIR", str(self.SAMPLE_ROOT))
        result = compute_insights("p01")
        subscription = next(insight for insight in result["insights"] if insight["id"] == "subscription_creep")
        names = [item["name"].lower() for item in subscription["subscriptions"]]

        assert names == [
            "figma professional monthly subscription",
            "spotify monthly subscription",
            "netflix monthly subscription",
        ]
        assert not any("rent" in name or "grocer" in name or "payroll" in name for name in names)

    def test_upload_fixtures_parse(self):
        upload_dir = self.SAMPLE_ROOT / "uploads"
        transactions = parse_transactions_csv((upload_dir / "sample_transactions.csv").read_bytes())
        calendar = parse_calendar_ics((upload_dir / "sample_calendar.ics").read_bytes())
        conversations = parse_chatgpt_export(
            (upload_dir / "sample_chatgpt_export.json").read_bytes(),
            "sample_chatgpt_export.json",
        )

        assert len(transactions) >= 30
        assert len(calendar) >= 15
        assert len(conversations) >= 5

    def test_upload_fixtures_generate_sensible_demo_insights(self):
        upload_dir = self.SAMPLE_ROOT / "uploads"
        transactions = parse_transactions_csv((upload_dir / "sample_transactions.csv").read_bytes())
        calendar = parse_calendar_ics((upload_dir / "sample_calendar.ics").read_bytes())
        conversations = parse_chatgpt_export(
            (upload_dir / "sample_chatgpt_export.json").read_bytes(),
            "sample_chatgpt_export.json",
        )

        result = compute_insights_from_dataframes(
            transactions_df=transactions,
            calendar_df=calendar,
            conversations_df=conversations,
            user_context={
                "income": 78000,
                "savingsGoal": 25000,
                "currentSavings": 8000,
                "monthlyDebt": 350,
            },
        )
        _validate_insight_schema(result)
        insights = {insight["id"]: insight for insight in result["insights"]}

        goal = insights["months_to_goal"]
        assert goal["months_to_goal"] == pytest.approx(56.7, abs=0.1)
        assert goal["avg_net_monthly_savings"] == 300
        assert goal["confidence"]["level"] == "high"

        day_of_week = insights["expensive_day_of_week"]
        assert day_of_week["expensive_day"] not in {"Monday", "Tuesday"}
        assert day_of_week["by_day"].get("Monday", 0) < 1000
        assert day_of_week["by_day"].get("Tuesday", 0) < 1000
        assert day_of_week["provenance"]["method"] == "discretionary_outflow_day_of_week_average_v1"
        assert any("Income deposits" in item for item in day_of_week["evidence"])

        surge = insights["post_payday_surge"]
        assert surge["detected"] is True
        assert surge["total_spend"] == pytest.approx(783.64, abs=0.01)
        assert surge["surge_pct"] == 35.0
        assert surge["provenance"]["method"] == "income_deposit_window_discretionary_spend_concentration_v1"

        velocity = insights["spending_velocity"]
        assert velocity["is_front_loaded"] is False
        assert velocity["first_half_pct"] == 45.0
        assert velocity["second_half_pct"] == 55.0
