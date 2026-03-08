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


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw)

    txn_frames: list[pd.DataFrame] = []
    cal_frames: list[pd.DataFrame] = []
    conv_frames: list[pd.DataFrame] = []

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

    transactions_df = pd.concat(txn_frames, ignore_index=True) if txn_frames else None
    calendar_df = pd.concat(cal_frames, ignore_index=True) if cal_frames else None
    conversations_df = pd.concat(conv_frames, ignore_index=True) if conv_frames else None

    user_context = payload.get("userContext") or None

    result = compute_insights_from_dataframes(
        transactions_df=transactions_df,
        calendar_df=calendar_df,
        conversations_df=conversations_df,
        user_context=user_context,
    )

    print(json.dumps(result))


if __name__ == "__main__":
    main()
