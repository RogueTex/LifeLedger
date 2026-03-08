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

    transactions_df = None
    calendar_df = None
    conversations_df = None

    for file_info in payload.get("files", []):
        file_bytes = base64.b64decode(file_info["data"])
        file_type = file_info["type"]
        filename = file_info.get("name", "")

        if file_type == "transactions":
            transactions_df = parse_transactions_csv(file_bytes)
        elif file_type == "calendar":
            calendar_df = parse_calendar_ics(file_bytes)
        elif file_type == "conversations":
            conversations_df = parse_chatgpt_export(file_bytes, filename)

    result = compute_insights_from_dataframes(
        transactions_df=transactions_df,
        calendar_df=calendar_df,
        conversations_df=conversations_df,
    )

    print(json.dumps(result))


if __name__ == "__main__":
    main()
