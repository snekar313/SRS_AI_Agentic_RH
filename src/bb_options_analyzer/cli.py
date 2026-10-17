from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from .analysis import analyze_rows


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Analyze exported BB option activity")
    result.add_argument("csv_file", type=Path)
    result.add_argument("--start", type=date.fromisoformat, required=True)
    result.add_argument("--end", type=date.fromisoformat, required=True)
    result.add_argument("--symbol", default="BB")
    return result


def main() -> int:
    args = parser().parse_args()
    with args.csv_file.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    result = analyze_rows(rows, args.start, args.end, args.symbol)
    print(json.dumps(result, indent=2))
    return 0
