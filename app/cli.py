"""Command-line interface for the CI/CD laboratory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from .core import make_metric


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--variant", required=True)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    result = {
        "variant": args.variant,
        "mode": args.mode,
        "rows": len(rows),
        "value": make_metric(rows, args.mode),
        "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Report generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
