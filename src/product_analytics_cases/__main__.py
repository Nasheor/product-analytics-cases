"""Command line entry point. ``python -m <pkg> smoke`` must finish in under 10 minutes and write
``results/smoke.json`` plus ``results/readme_numbers.json`` (label to value string, asserted against README.md).
Units replace the smoke body with their real run and keep the two output files."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"


def smoke() -> int:
    RESULTS.mkdir(exist_ok=True)
    out = {"smoke_ok": "yes", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    (RESULTS / "smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (RESULTS / "readme_numbers.json").write_text(json.dumps({"smoke_ok": "yes"}, indent=2), encoding="utf-8")
    print("smoke ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pkg")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("smoke", help="short reproducible run that regenerates results/")
    args = p.parse_args(argv)
    if args.cmd == "smoke":
        return smoke()
    return 2


if __name__ == "__main__":
    sys.exit(main())
