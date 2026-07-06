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
    detect_upload_type,
    parse_calendar_ics,
    parse_chatgpt_export,
    parse_transactions_csv,
)
from src.insights.insight_engine import compute_insights_from_dataframes

CONCRETE_FILE_TYPES = {"transactions", "calendar", "conversations"}
ALLOWED_FILE_TYPES = CONCRETE_FILE_TYPES | {"auto"}


def _emit_error(message: str, code: str = "upload_processing_error") -> None:
    print(json.dumps({"error": message, "error_code": code}))


def _append_frame(frames: list[pd.DataFrame], df: pd.DataFrame, filename: str, detected_type: str) -> int:
    if df.empty:
        return 0
    annotated = df.copy()
    annotated["source_file"] = filename or "unnamed file"
    annotated["detected_upload_type"] = detected_type
    frames.append(annotated)
    return int(len(annotated))


def _renumber_ids(df: pd.DataFrame | None, prefix: str) -> pd.DataFrame | None:
    if df is None or df.empty:
        return df
    out = df.copy().reset_index(drop=True)
    out["id"] = [f"{prefix}_{idx:04d}" for idx in range(len(out))]
    return out


def _frame_count(df: pd.DataFrame | None) -> int:
    return 0 if df is None or df.empty else int(len(df))


def _conversation_provider_counts(df: pd.DataFrame | None) -> dict[str, int]:
    if df is None or df.empty or "provider" not in df.columns:
        return {}
    counts = df["provider"].dropna().astype(str).value_counts().to_dict()
    return {provider: int(count) for provider, count in counts.items()}


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
    file_summaries: list[dict[str, object]] = []

    try:
        for file_info in payload.get("files", []):
            file_type = file_info.get("type", "auto")
            filename = file_info.get("name", "")
            if file_type not in ALLOWED_FILE_TYPES:
                _emit_error(f"Unsupported file type: {file_type}.", "unsupported_file_type")
                sys.exit(1)

            file_bytes = base64.b64decode(file_info["data"], validate=True)
            if not file_bytes:
                _emit_error(f"Uploaded file is empty: {filename or 'unnamed file'}.", "empty_file")
                sys.exit(1)

            detected_type = detect_upload_type(
                file_bytes,
                filename,
                hinted_type=file_type if file_type in CONCRETE_FILE_TYPES else None,
            )
            if detected_type not in CONCRETE_FILE_TYPES:
                _emit_error(
                    f"Could not detect a supported data type for {filename or 'unnamed file'}.",
                    "unsupported_file_type",
                )
                sys.exit(1)

            if detected_type == "transactions":
                df = parse_transactions_csv(file_bytes)
                rows = _append_frame(txn_frames, df, filename, detected_type)
            elif detected_type == "calendar":
                df = parse_calendar_ics(file_bytes)
                rows = _append_frame(cal_frames, df, filename, detected_type)
            elif detected_type == "conversations":
                df = parse_chatgpt_export(file_bytes, filename)
                rows = _append_frame(conv_frames, df, filename, detected_type)
            else:
                rows = 0

            if rows == 0:
                _emit_error(f"No usable {detected_type} rows found in {filename or 'unnamed file'}.", "empty_parsed_file")
                sys.exit(1)

            file_summaries.append({
                "name": filename,
                "declared_type": file_type,
                "detected_type": detected_type,
                "rows": rows,
            })
    except KeyError as exc:
        _emit_error(f"Missing expected file field: {exc}.", "invalid_file_payload")
        sys.exit(1)
    except (ValueError, TypeError, base64.binascii.Error):
        _emit_error("One or more files could not be decoded.", "invalid_file_encoding")
        sys.exit(1)

    transactions_df = _renumber_ids(pd.concat(txn_frames, ignore_index=True), "t") if txn_frames else None
    calendar_df = _renumber_ids(pd.concat(cal_frames, ignore_index=True), "cal") if cal_frames else None
    conversations_df = _renumber_ids(pd.concat(conv_frames, ignore_index=True), "c") if conv_frames else None

    ingestion_summary = {
        "files": file_summaries,
        "source_rows": {
            "transactions": _frame_count(transactions_df),
            "calendar_events": _frame_count(calendar_df),
            "conversation_messages": _frame_count(conversations_df),
        },
        "conversation_providers": _conversation_provider_counts(conversations_df),
    }

    user_context = payload.get("userContext") or None

    try:
        result = compute_insights_from_dataframes(
            transactions_df=transactions_df,
            calendar_df=calendar_df,
            conversations_df=conversations_df,
            user_context=user_context,
        )
        result["ingestion_summary"] = ingestion_summary
    except Exception as exc:
        _emit_error(f"Failed to compute insights: {exc}", "insight_compute_failed")
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
