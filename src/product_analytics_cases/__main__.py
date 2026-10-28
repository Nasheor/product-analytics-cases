"""Command line entry point.

``python -m product_analytics_cases download [olist|upworthy]`` fetches the raw data.
``python -m product_analytics_cases run`` executes the three ``analysis.py`` files, syncs and executes
the notebooks, and writes ``results/summary.json`` plus ``results/readme_numbers.json``.
``python -m product_analytics_cases smoke`` is the same run on the cached raw data (it downloads the
data when it is missing) and must finish in under 10 minutes. It also writes ``results/smoke.json``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

from . import download as dl
from .common import CASES, RESULTS, load_results, raw_present

CASE_DIRS = ["01_funnel_retention", "02_experiment_readout", "03_metric_definition_review"]
CASE_KEYS = {"01_funnel_retention": "case1", "02_experiment_readout": "case2", "03_metric_definition_review": "case3"}


def _run(cmd: list[str], cwd: Path) -> None:
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-4000:], file=sys.stderr)
        print(r.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    for line in r.stdout.strip().splitlines()[-3:]:
        print("  ", line)


KERNEL = "product-analytics-cases"


def ensure_kernel() -> None:
    """Register this interpreter as a Jupyter kernel inside its own prefix, so the notebooks run on the
    repo's environment and not on whichever python3 kernel is registered elsewhere on the machine."""
    spec = Path(sys.prefix) / "share" / "jupyter" / "kernels" / KERNEL / "kernel.json"
    if not spec.exists():
        _run([sys.executable, "-m", "ipykernel", "install", "--prefix", sys.prefix, "--name", KERNEL,
              "--display-name", "Python (product-analytics-cases)"], CASES.parent)


def ensure_data() -> None:
    for ds in ("olist", "upworthy"):
        if not raw_present(ds):
            dl.download(ds)


def memo_words(case_dir: Path) -> int:
    return len((case_dir / "memo.md").read_text(encoding="utf-8").split())


def notebook_executed(case_dir: Path) -> bool:
    path = case_dir / "notebook.ipynb"
    if not path.exists():
        return False
    nb = json.loads(path.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    if not code:
        return False
    for c in code:
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                return False
    return any(c.get("execution_count") for c in code)


def build_summary() -> dict:
    sources = json.loads((RESULTS / "data_sources.json").read_text(encoding="utf-8"))
    rows = []
    readme_numbers: dict[str, str] = {}
    for name in CASE_DIRS:
        case_dir = CASES / name
        key = CASE_KEYS[name]
        res = load_results(key)
        notes = res["notes"]
        rows_read = int(res["numbers"]["rows_read"]["value"])
        words = memo_words(case_dir)
        executed = notebook_executed(case_dir)
        rows.append({"case": name, "dataset": notes["dataset"], "licence": notes["licence"], "rows_read": rows_read,
                     "headline": notes["headline"], "recommendation": notes["recommendation"],
                     "memo_words": words, "notebook_executed": "yes" if executed else "no"})
        readme_numbers[f"{key}_rows_read"] = f"{rows_read:,}"
        readme_numbers[f"{key}_headline"] = notes["headline"]
        readme_numbers[f"{key}_memo_words"] = str(words)
        readme_numbers[f"{key}_notebook"] = "yes" if executed else "no"
    return {"generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "data_sources": {k: {"rows_total": v["rows_total"], "files": len(v["files"])} for k, v in sources.items()},
            "cases": rows, "readme_numbers": readme_numbers}


def run(skip_notebooks: bool = False) -> int:
    t0 = time.time()
    ensure_data()
    RESULTS.mkdir(exist_ok=True)
    for name in CASE_DIRS:
        _run([sys.executable, "analysis.py"], CASES / name)
    if not skip_notebooks:
        ensure_kernel()
        for name in CASE_DIRS:
            case_dir = CASES / name
            _run([sys.executable, "-m", "jupytext", "--sync", "notebook.py"], case_dir)
            _run([sys.executable, "-m", "nbconvert", "--execute", "--to", "notebook", "--inplace",
                  f"--ExecutePreprocessor.kernel_name={KERNEL}", "--ExecutePreprocessor.timeout=600",
                  "notebook.ipynb"], case_dir)
    summary = build_summary()
    summary["seconds"] = round(time.time() - t0, 1)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (RESULTS / "readme_numbers.json").write_text(json.dumps(summary["readme_numbers"], indent=2), encoding="utf-8")
    print(f"run finished in {summary['seconds']} s")
    return 0


def smoke() -> int:
    rc = run()
    out = {"smoke_ok": "yes" if rc == 0 else "no",
           "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds")}
    (RESULTS / "smoke.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("smoke ok")
    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="product_analytics_cases")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download", help="fetch the raw data into data/raw/")
    d.add_argument("dataset", nargs="*", default=["olist", "upworthy"])
    d.add_argument("--force", action="store_true")
    r = sub.add_parser("run", help="run the three analyses and execute the notebooks")
    r.add_argument("--skip-notebooks", action="store_true")
    sub.add_parser("smoke", help="short reproducible run that regenerates results/")
    args = p.parse_args(argv)
    if args.cmd == "download":
        for ds in args.dataset:
            dl.download(ds, force=args.force)
        return 0
    if args.cmd == "run":
        return run(skip_notebooks=args.skip_notebooks)
    if args.cmd == "smoke":
        return smoke()
    return 2


if __name__ == "__main__":
    sys.exit(main())
