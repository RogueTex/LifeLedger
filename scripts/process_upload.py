"""Process uploaded files and return insight JSON via stdout.

Called by the Express server. Reads a JSON payload from stdin containing
base64-encoded file data, parses each file, computes insights, and prints
the result as JSON to stdout.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pandas as pd

# Ensure project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.loaders.upload_parser import (
    parse_calendar_ics,
    parse_chatgpt_export,
    parse_transactions_csv,
)
from src.insights.insight_engine import compute_insights_from_dataframes


def _emit_error(message: str, code: str = "upload_processing_error") -> None:
    print(json.dumps({"error": message, "error_code": code}))


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _emit_error("Request payload is not valid JSON.", "invalid_json")
        sys.exit(1)

    txn_frames: list[pd.DataFrame] = []
    cal_frames: list[pd.DataFrame] = []
    conv_frames: list[pd.DataFrame] = []

    try:
        for file_info in payload.get("files", []):
            file_bytes = base64.b64decode(file_info["data"])
            file_type = file_info["type"]
            filename = file_info.get("name", "")

            if file_type == "transactions":
                df = parse_transactions_csv(file_bytes)
                if not df.empty:
                    txn_frames.append(df)
            elif file_type == "calendar":
                df = parse_calendar_ics(file_bytes)
                if not df.empty:
                    cal_frames.append(df)
            elif file_type == "conversations":
                df = parse_chatgpt_export(file_bytes, filename)
                if not df.empty:
                    conv_frames.append(df)
    except KeyError as exc:
        _emit_error(f"Missing expected file field: {exc}.", "invalid_file_payload")
        sys.exit(1)
    except (ValueError, TypeError, base64.binascii.Error):
        _emit_error("One or more files could not be decoded.", "invalid_file_encoding")
        sys.exit(1)

    transactions_df = pd.concat(txn_frames, ignore_index=True) if txn_frames else None
    calendar_df = pd.concat(cal_frames, ignore_index=True) if cal_frames else None
    conversations_df = pd.concat(conv_frames, ignore_index=True) if conv_frames else None

    user_context = payload.get("userContext") or None

    try:
        result = compute_insights_from_dataframes(
            transactions_df=transactions_df,
            calendar_df=calendar_df,
            conversations_df=conversations_df,
            user_context=user_context,
        )
    except Exception as exc:
        _emit_error(f"Failed to compute insights: {exc}", "insight_compute_failed")
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
